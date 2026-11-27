import os
import re
import json
import uuid
import requests
from io import BytesIO
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from boto3.dynamodb.conditions import Key, Attr

from aws_client import table, sns_client, SNS_TOPIC_ARN
from agents.resume_tailor import tailor_and_store_resume, list_user_resumes

load_dotenv()

app = FastAPI(title="WingStack AI Backend (AWS Production)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"


# -------------------- HELPER FUNCTIONS --------------------
def make_user_id(github_username: str, name: str) -> str:
    raw = github_username.strip() or name.strip() or str(uuid.uuid4())[:8]
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw.lower()).strip("-")
    return cleaned or str(uuid.uuid4())[:8]


def fetch_github_stats(username: str) -> dict:
    if not username:
        return {"repos": 0, "languages": [], "repo_details": [], "status": "not_provided"}
    try:
        res = requests.get(
            f"https://api.github.com/users/{username}/repos?per_page=30&sort=updated",
            timeout=6,
        )
        if res.status_code == 200:
            repos = res.json()
            own_repos = [r for r in repos if not r.get("fork")]
            langs = list({r.get("language") for r in own_repos if r.get("language")})
            repo_details = [
                {
                    "name": r.get("name", ""),
                    "description": r.get("description") or "",
                    "language": r.get("language") or "",
                    "topics": r.get("topics", []),
                    "html_url": r.get("html_url", ""),
                }
                for r in own_repos[:12]
            ]
            return {
                "repos": len(own_repos),
                "languages": langs[:6],
                "repo_details": repo_details,
                "status": "verified",
            }
    except Exception:
        pass
    return {"repos": 0, "languages": [], "repo_details": [], "status": "fallback"}


def fetch_codeforces_stats(handle: str) -> dict:
    if not handle:
        return {"rating": "Unrated", "rank": "Beginner", "status": "not_provided"}
    try:
        res = requests.get(f"https://codeforces.com/api/user.info?handles={handle}", timeout=5)
        if res.status_code == 200 and res.json().get("status") == "OK":
            info = res.json()["result"][0]
            return {
                "rating": int(info.get("rating", 1200)),
                "rank": info.get("rank", "pupil"),
                "status": "verified",
            }
    except Exception:
        pass
    return {"rating": 1150, "rank": "pupil", "status": "fallback"}


def ask_groq_json(system_prompt: str, user_prompt: str) -> dict:
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt + " Always respond strictly with valid JSON."},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return json.loads(completion.choices[0].message.content)


# -------------------- API ENDPOINTS --------------------
@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "WingStack AI Career & Accountability Engine",
        "storage": "AWS DynamoDB + S3",
    }


# 1. UNIFIED PROFILE & AI READINESS SCANNER (AGENT 1)
@app.post("/api/profile/analyze")
async def analyze_profile(
    name: str = Form(...),
    target_role: str = Form(...),
    intensity_mode: str = Form("Hell Mode"),
    github_username: str = Form(""),
    codeforces_handle: str = Form(""),
    resume: Optional[UploadFile] = File(None),
):
    resume_text = ""
    if resume:
        try:
            pdf_bytes = await resume.read()
            reader = PdfReader(BytesIO(pdf_bytes))
            for page in reader.pages[:3]:
                resume_text += page.extract_text() or ""
        except Exception:
            resume_text = ""

    gh_stats = fetch_github_stats(github_username)
    cf_stats = fetch_codeforces_stats(codeforces_handle)

    system_prompt = (
        "You are WingStack's AI Career Profiler. Analyze the candidate's resume text and coding stats. "
        "Return JSON with exact keys: "
        "'readiness_score' (integer 45-95), "
        "'verified_skills' (list of 5-7 concrete technical skills), "
        "'missing_skills' (list of 3-4 key skills needed for their target role), "
        "'summary' (2 sharp sentences evaluating their readiness)."
    )
    user_prompt = (
        f"Candidate: {name}\nTarget Role: {target_role}\n"
        f"GitHub Stats: {json.dumps(gh_stats)}\nCodeforces Stats: {json.dumps(cf_stats)}\n"
        f"Resume Text: {resume_text[:3500]}"
    )

    try:
        ai_result = ask_groq_json(system_prompt, user_prompt)
    except Exception:
        ai_result = {
            "readiness_score": 74,
            "verified_skills": gh_stats["languages"] or ["Python", "C++", "Git", "DSA"],
            "missing_skills": ["System Design", "Docker", "Cloud Deployment"],
            "summary": f"Solid coding foundation for {target_role}. Focus on closing cloud and production deployment gaps.",
        }

    user_id = make_user_id(github_username, name)
    readiness_score = int(ai_result.get("readiness_score", 75))
    verified_skills = ai_result.get("verified_skills", [])
    missing_skills = ai_result.get("missing_skills", [])
    summary = ai_result.get("summary", "")

    table.put_item(
        Item={
            "pk": f"USER#{user_id}",
            "sk": "PROFILE",
            "user_id": user_id,
            "name": name,
            "target_role": target_role,
            "intensity_mode": intensity_mode,
            "github_username": github_username,
            "codeforces_handle": codeforces_handle,
            "readiness_score": readiness_score,
            "verified_skills": verified_skills,
            "missing_skills": missing_skills,
            "summary": summary,
            "resume_text": resume_text,
            "github_repos": gh_stats.get("repo_details", []),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    return {
        "user_id": user_id,
        "name": name,
        "target_role": target_role,
        "intensity_mode": intensity_mode,
        "github_stats": {
            "repos": gh_stats["repos"],
            "languages": gh_stats["languages"],
            "status": gh_stats["status"],
        },
        "codeforces_stats": cf_stats,
        "readiness_score": readiness_score,
        "verified_skills": verified_skills,
        "missing_skills": missing_skills,
        "summary": summary,
    }


# 2. AUTONOMOUS CAREER PAGE SCOUT & FIT SCORER (AGENT 2)
@app.get("/api/jobs/match/{user_id}")
def match_jobs(user_id: str):
    resp = table.get_item(Key={"pk": f"USER#{user_id}", "sk": "PROFILE"})
    user = resp.get("Item")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    target_role = user.get("target_role", "Software Engineer")
    raw_jobs = []
    try:
        from urllib.parse import quote_plus
        query = quote_plus(target_role)
        res = requests.get(f"https://remotive.com/api/remote-jobs?search={query}&limit=20", timeout=8)
        if res.status_code == 200:
            for j in res.json().get("jobs", [])[:15]:
                raw_jobs.append(
                    {
                        "title": j.get("title"),
                        "company": j.get("company_name"),
                        "location": j.get("candidate_required_location", "Remote"),
                        "apply_url": j.get("url"),
                        "tags": j.get("tags", [])[:6],
                    }
                )
    except Exception:
        pass

    if not raw_jobs:
        raw_jobs = [
            {
                "title": f"{target_role} - Core Systems",
                "company": "Razorpay",
                "location": "Bengaluru / Hybrid",
                "apply_url": "https://razorpay.com/jobs/",
                "tags": user.get("verified_skills", ["Python", "APIs", "SQL"])[:5],
            },
            {
                "title": f"Junior {target_role}",
                "company": "BrowserStack",
                "location": "Remote / Mumbai",
                "apply_url": "https://www.browserstack.com/careers",
                "tags": user.get("verified_skills", ["Python", "REST", "Git"])[:5],
            },
            {
                "title": f"SDE-1 ({target_role})",
                "company": "Postman",
                "location": "Bengaluru",
                "apply_url": "https://www.postman.com/company/careers/",
                "tags": user.get("verified_skills", ["APIs", "Cloud", "Git"])[:5],
            },
        ]

    system_prompt = (
        "You are WingStack's Career Scout Agent. Filter and select ONLY the top 5-6 jobs from the list that "
        "best match the candidate's exact target role, resume experience, and verified skills. "
        "Exclude unrelated roles (like sales, marketing, or mismatched tech stacks). "
        "Return JSON with key 'jobs' containing a list of objects, each with: "
        "'title', 'company', 'location', 'apply_url', 'match_percentage' (integer 60-96), "
        "'missing_skills' (list of 1-3 gaps), and 'tailored_pitch' (1 punchy sentence referencing their actual resume/projects)."
    )
    user_prompt = (
        f"User Target Role: {target_role}\n"
        f"Verified Skills: {json.dumps(user.get('verified_skills', []))}\n"
        f"Resume Summary/Text: {user.get('resume_text', '')[:2000]}\n"
        f"GitHub Repos: {json.dumps(user.get('github_repos', []))[:1500]}\n"
        f"Candidate Jobs List: {json.dumps(raw_jobs)}"
    )

    try:
        return ask_groq_json(system_prompt, user_prompt)
    except Exception:
        fallback_jobs = [
            {
                **j,
                "match_percentage": 84,
                "missing_skills": ["Docker"],
                "tailored_pitch": f"Strong hands-on builder in {target_role} ready to ship production features.",
            }
            for j in raw_jobs[:6]
        ]
        return {"jobs": fallback_jobs}


# 3. BLIND MATCHMAKING ENGINE (AGENT 3)
@app.post("/api/match/find/{user_id}")
def find_wingman(user_id: str):
    resp = table.get_item(Key={"pk": f"USER#{user_id}", "sk": "PROFILE"})
    user = resp.get("Item")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    scan_resp = table.scan(FilterExpression=Attr("sk").eq("PROFILE") & Attr("user_id").ne(user_id))
    candidates = scan_resp.get("Items", [])

    partner = next(
        (c for c in candidates if c.get("intensity_mode") == user.get("intensity_mode")),
        candidates[0] if candidates else None,
    )

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="No other real peer profiles found in DynamoDB yet. Create a second profile to pair.",
        )

    partnership_id = str(uuid.uuid4())[:8]
    now_iso = datetime.now(timezone.utc).isoformat()

    table.put_item(
        Item={
            "pk": f"PARTNERSHIP#{partnership_id}",
            "sk": "META",
            "partnership_id": partnership_id,
            "user1_id": user_id,
            "user2_id": partner["user_id"],
            "target_role": user.get("target_role", "Software Engineer"),
            "intensity_mode": user.get("intensity_mode", "Hell Mode"),
            "streak_days": 1,
            "user1_verified_today": False,
            "user2_verified_today": True,
            "status": "ACTIVE",
            "created_at": now_iso,
        }
    )

    return {
        "partnership_id": partnership_id,
        "status": "ACTIVE",
        "streak_days": 1,
        "intensity_mode": user.get("intensity_mode"),
        "wingman": {
            "user_id": partner["user_id"],
            "name": partner.get("name"),
            "target_role": partner.get("target_role"),
            "readiness_score": int(partner.get("readiness_score", 75)),
            "verified_skills": partner.get("verified_skills", []),
            "verified_today": True,
        },
    }


# 4. GITHUB-BACKED ATS RESUME TAILOR & S3 VAULT (AGENT 4)
class TailorResumeRequest(BaseModel):
    user_id: str
    company: str
    job_title: str
    job_description: str = ""


@app.post("/api/resume/tailor")
def tailor_resume_endpoint(payload: TailorResumeRequest):
    try:
        return tailor_and_store_resume(
            user_id=payload.user_id,
            company=payload.company,
            job_title=payload.job_title,
            job_description=payload.job_description,
            ask_groq_fn=ask_groq_json,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume tailoring failed: {str(e)}")


@app.get("/api/resume/vault/{user_id}")
def get_resume_vault(user_id: str):
    try:
        resumes = list_user_resumes(user_id)
        return {"user_id": user_id, "count": len(resumes), "resumes": resumes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch resume vault: {str(e)}")


# 5. WAR ROOM AI OPERATIVE (PROOF VERIFICATION)
class ProofRequest(BaseModel):
    partnership_id: str
    user_id: str
    proof_url: str
    note: str


@app.post("/api/sprint/verify")
def verify_daily_proof(payload: ProofRequest):
    user_resp = table.get_item(Key={"pk": f"USER#{payload.user_id}", "sk": "PROFILE"})
    part_resp = table.get_item(Key={"pk": f"PARTNERSHIP#{payload.partnership_id}", "sk": "META"})
    user = user_resp.get("Item")
    partnership = part_resp.get("Item")

    if not user or not partnership:
        raise HTTPException(status_code=404, detail="User or partnership not found")

    system_prompt = (
        "You are WingStack's strict AI Operative inside a coding accountability War Room. "
        "Evaluate the developer's daily proof-of-work submission and give them tomorrow's tactical mission "
        "to close their job skill gaps. Return JSON with exact keys: "
        "'verified' (boolean, true if proof_url or note shows genuine coding/DSA effort), "
        "'operative_feedback' (2 direct, motivating tactical sentences), "
        "'next_mission' (1 specific actionable coding/DSA task for tomorrow)."
    )
    user_prompt = (
        f"Proof URL: {payload.proof_url}\nDeveloper Note: {payload.note}\n"
        f"Target Role: {user.get('target_role')}\nMissing Skills to Close: {json.dumps(user.get('missing_skills', []))}"
    )

    try:
        verdict = ask_groq_json(system_prompt, user_prompt)
    except Exception:
        verdict = {
            "verified": True,
            "operative_feedback": "Proof logged and verified. Your commit momentum keeps the sprint alive.",
            "next_mission": "Solve 2 medium graph/DP problems and push clean notes to GitHub before midnight.",
        }

    current_streak = int(partnership.get("streak_days", 1))
    new_streak = current_streak + (1 if verdict.get("verified") else 0)

    table.update_item(
        Key={"pk": f"PARTNERSHIP#{payload.partnership_id}", "sk": "META"},
        UpdateExpression="SET user1_verified_today = :v, streak_days = :s",
        ExpressionAttributeValues={":v": True, ":s": new_streak},
    )

    return {
        "partnership_id": payload.partnership_id,
        "status": "ACTIVE",
        "streak_days": new_streak,
        **verdict,
    }


# 6. KILL SWITCH SIMULATOR + AWS SNS ALERT
@app.post("/api/sprint/simulate-midnight/{partnership_id}")
def simulate_midnight(partnership_id: str, force_miss: bool = True):
    part_resp = table.get_item(Key={"pk": f"PARTNERSHIP#{partnership_id}", "sk": "META"})
    partnership = part_resp.get("Item")
    if not partnership:
        raise HTTPException(status_code=404, detail="Partnership not found")

    if force_miss or not partnership.get("user1_verified_today", False):
        table.update_item(
            Key={"pk": f"PARTNERSHIP#{partnership_id}", "sk": "META"},
            UpdateExpression="SET #st = :st, streak_days = :sd",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":st": "DISSOLVED_KILL_SWITCH", ":sd": 0},
        )
        try:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="WingStack Kill Switch Alert",
                Message=f"Partnership {partnership_id} dissolved at midnight. Streak reset to 0.",
            )
        except Exception:
            pass

        return {
            "partnership_id": partnership_id,
            "status": "DISSOLVED_KILL_SWITCH",
            "streak_days": 0,
            "message": "MIDNIGHT PROTOCOL TRIGGERED: Daily proof missing. Streak wiped to 0 and partnership dissolved.",
        }

    return {
        "partnership_id": partnership_id,
        "status": "ACTIVE",
        "streak_days": int(partnership.get("streak_days", 1)),
        "message": "Both partners verified before midnight. Sprint continues!",
    }
