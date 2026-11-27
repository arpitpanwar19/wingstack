import os
import json
import sqlite3
import requests
from io import BytesIO
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader

load_dotenv()

app = FastAPI(title="WingStack AI Backend")

# Allow React frontend (localhost + AWS Amplify) to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"
DB_PATH = "wingstack.db"


# -------------------- DATABASE SETUP --------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_role TEXT NOT NULL,
            intensity_mode TEXT NOT NULL,
            github_username TEXT,
            codeforces_handle TEXT,
            readiness_score INTEGER DEFAULT 70,
            verified_skills TEXT DEFAULT '[]',
            missing_skills TEXT DEFAULT '[]',
            summary TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS partnerships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            target_role TEXT NOT NULL,
            intensity_mode TEXT NOT NULL,
            streak_days INTEGER DEFAULT 1,
            user1_verified_today INTEGER DEFAULT 0,
            user2_verified_today INTEGER DEFAULT 1,
            status TEXT DEFAULT 'ACTIVE'
        )
    """)

    # Seed realistic peers if DB is empty so Blind Matchmaking works immediately
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    if cur.fetchone()["cnt"] == 0:
        seed_peers = [
            ("Rohan Verma", "Backend Developer", "Hell Mode", "rohan-dev", "rohan_cf", 78,
             json.dumps(["Python", "FastAPI", "SQL", "Git", "DSA"]), json.dumps(["Docker", "AWS"]),
             "Strong algorithmic thinker building scalable Python APIs."),
            ("Ananya Sharma", "Full Stack Developer", "Weekend Warrior", "ananya-codes", "ananya_cp", 82,
             json.dumps(["React", "JavaScript", "Node.js", "Tailwind"]), json.dumps(["System Design", "Testing"]),
             "Frontend-focused builder shipping clean web applications."),
            ("Kabir Nair", "Backend Developer", "Weekend Warrior", "kabir-sys", "kabir99", 74,
             json.dumps(["C++", "Python", "REST APIs", "MySQL"]), json.dumps(["Redis", "CI/CD"]),
             "Competitive programmer transitioning into backend engineering."),
            ("Meera Joshi", "Full Stack Developer", "Hell Mode", "meera-stack", "meeracodes", 85,
             json.dumps(["React", "Python", "PostgreSQL", "TypeScript"]), json.dumps(["Kubernetes", "AWS"]),
             "High-intensity builder shipping full-stack MVP projects weekly.")
        ]
        cur.executemany("""
            INSERT INTO users (name, target_role, intensity_mode, github_username, codeforces_handle,
                               readiness_score, verified_skills, missing_skills, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_peers)

    conn.commit()
    conn.close()


init_db()


# -------------------- HELPER FUNCTIONS --------------------
def fetch_github_stats(username: str) -> dict:
    if not username:
        return {"repos": 0, "languages": [], "status": "not_provided"}
    try:
        res = requests.get(f"https://api.github.com/users/{username}/repos?per_page=30", timeout=5)
        if res.status_code == 200:
            repos = res.json()
            langs = list({r.get("language") for r in repos if r.get("language")})
            return {"repos": len(repos), "languages": langs[:6], "status": "verified"}
    except Exception:
        pass
    return {"repos": 4, "languages": ["Python", "JavaScript"], "status": "fallback"}


def fetch_codeforces_stats(handle: str) -> dict:
    if not handle:
        return {"rating": "Unrated", "rank": "Beginner", "status": "not_provided"}
    try:
        res = requests.get(f"https://codeforces.com/api/user.info?handles={handle}", timeout=5)
        if res.status_code == 200 and res.json().get("status") == "OK":
            info = res.json()["result"][0]
            return {
                "rating": info.get("rating", 1200),
                "rank": info.get("rank", "pupil"),
                "status": "verified"
            }
    except Exception:
        pass
    return {"rating": 1150, "rank": "pupil", "status": "fallback"}


def ask_groq_json(system_prompt: str, user_prompt: str) -> dict:
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt + " Always respond strictly with valid JSON."},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    return json.loads(completion.choices[0].message.content)


# -------------------- API ENDPOINTS --------------------
@app.get("/")
def health_check():
    return {"status": "online", "service": "WingStack AI Career & Accountability Engine"}


# 1. UNIFIED PROFILE & AI READINESS SCANNER
@app.post("/api/profile/analyze")
async def analyze_profile(
    name: str = Form(...),
    target_role: str = Form(...),
    intensity_mode: str = Form("Hell Mode"),
    github_username: str = Form(""),
    codeforces_handle: str = Form(""),
    resume: Optional[UploadFile] = File(None)
):
    resume_text = ""
    if resume:
        try:
            pdf_bytes = await resume.read()
            reader = PdfReader(BytesIO(pdf_bytes))
            for page in reader.pages[:3]:
                resume_text += page.extract_text() or ""
        except Exception:
            resume_text = "Resume uploaded (text extraction fallback)."

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
        f"Resume Text: {resume_text[:3000]}"
    )

    try:
        ai_result = ask_groq_json(system_prompt, user_prompt)
    except Exception:
        ai_result = {
            "readiness_score": 74,
            "verified_skills": gh_stats["languages"] or ["Python", "C++", "Git", "DSA"],
            "missing_skills": ["System Design", "Docker", "Cloud Deployment"],
            "summary": f"Solid coding foundation for {target_role}. Focus on closing cloud and production deployment gaps."
        }

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, target_role, intensity_mode, github_username, codeforces_handle,
                           readiness_score, verified_skills, missing_skills, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, target_role, intensity_mode, github_username, codeforces_handle,
        ai_result.get("readiness_score", 75),
        json.dumps(ai_result.get("verified_skills", [])),
        json.dumps(ai_result.get("missing_skills", [])),
        ai_result.get("summary", "")
    ))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "name": name,
        "target_role": target_role,
        "intensity_mode": intensity_mode,
        "github_stats": gh_stats,
        "codeforces_stats": cf_stats,
        **ai_result
    }


# 2. AUTONOMOUS CAREER PAGE SCOUT & FIT SCORER
@app.get("/api/jobs/match/{user_id}")
def match_jobs(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    raw_jobs = []
    try:
        res = requests.get("https://remotive.com/api/remote-jobs?category=software-dev&limit=8", timeout=6)
        if res.status_code == 200:
            for j in res.json().get("jobs", [])[:6]:
                raw_jobs.append({
                    "title": j.get("title"),
                    "company": j.get("company_name"),
                    "location": j.get("candidate_required_location", "Remote"),
                    "apply_url": j.get("url"),
                    "tags": j.get("tags", [])[:5]
                })
    except Exception:
        pass

    if not raw_jobs:
        raw_jobs = [
            {"title": "Software Engineer - Backend", "company": "Razorpay", "location": "Bengaluru / Hybrid",
             "apply_url": "https://razorpay.com/jobs/", "tags": ["Python", "APIs", "SQL"]},
            {"title": "SDE-1 (Full Stack)", "company": "BrowserStack", "location": "Remote / Mumbai",
             "apply_url": "https://www.browserstack.com/careers", "tags": ["React", "Node.js", "REST"]},
            {"title": "Junior Backend Developer", "company": "Postman", "location": "Bengaluru",
             "apply_url": "https://www.postman.com/company/careers/", "tags": ["JavaScript", "APIs", "Git"]}
        ]

    system_prompt = (
        "You are WingStack's Career Scout Agent. Score how well each job fits the user's skills. "
        "Return JSON with key 'jobs' containing a list of objects, each with: "
        "'title', 'company', 'location', 'apply_url', 'match_percentage' (integer 60-96), "
        "'missing_skills' (list of 1-3 gaps), and 'tailored_pitch' (1 punchy sentence to use when applying)."
    )
    user_prompt = (
        f"User Target Role: {user['target_role']}\n"
        f"User Skills: {user['verified_skills']}\n"
        f"Jobs List: {json.dumps(raw_jobs)}"
    )

    try:
        scored = ask_groq_json(system_prompt, user_prompt)
        return scored
    except Exception:
        fallback_jobs = [
            {**j, "match_percentage": 84, "missing_skills": ["Docker"],
             "tailored_pitch": f"Strong hands-on builder in {user['target_role']} ready to ship production features."}
            for j in raw_jobs
        ]
        return {"jobs": fallback_jobs}


# 3. BLIND MATCHMAKING ENGINE
@app.post("/api/match/find/{user_id}")
def find_wingman(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Find a peer with matching intensity or role (excluding current user)
    partner = conn.execute(
        "SELECT * FROM users WHERE id != ? AND intensity_mode = ? LIMIT 1",
        (user_id, user["intensity_mode"])
    ).fetchone()
    if not partner:
        partner = conn.execute("SELECT * FROM users WHERE id != ? LIMIT 1", (user_id,)).fetchone()

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO partnerships (user1_id, user2_id, target_role, intensity_mode, streak_days, user1_verified_today, user2_verified_today, status)
        VALUES (?, ?, ?, ?, 1, 0, 1, 'ACTIVE')
    """, (user_id, partner["id"], user["target_role"], user["intensity_mode"]))
    partnership_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "partnership_id": partnership_id,
        "status": "ACTIVE",
        "streak_days": 1,
        "intensity_mode": user["intensity_mode"],
        "wingman": {
            "name": partner["name"],
            "target_role": partner["target_role"],
            "readiness_score": partner["readiness_score"],
            "verified_skills": json.loads(partner["verified_skills"]),
            "verified_today": True
        }
    }


# 4. WAR ROOM AI OPERATIVE (PROOF VERIFICATION)
class ProofRequest(BaseModel):
    partnership_id: int
    user_id: int
    proof_url: str
    note: str


@app.post("/api/sprint/verify")
def verify_daily_proof(payload: ProofRequest):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (payload.user_id,)).fetchone()
    partnership = conn.execute("SELECT * FROM partnerships WHERE id = ?", (payload.partnership_id,)).fetchone()
    if not user or not partnership:
        conn.close()
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
        f"Target Role: {user['target_role']}\nMissing Skills to Close: {user['missing_skills']}"
    )

    try:
        verdict = ask_groq_json(system_prompt, user_prompt)
    except Exception:
        verdict = {
            "verified": True,
            "operative_feedback": "Proof logged and verified. Your commit momentum keeps the sprint alive.",
            "next_mission": "Solve 2 medium graph/DP problems and push clean notes to GitHub before midnight."
        }

    new_streak = partnership["streak_days"] + (1 if verdict.get("verified") else 0)
    conn.execute(
        "UPDATE partnerships SET user1_verified_today = 1, streak_days = ? WHERE id = ?",
        (new_streak, payload.partnership_id)
    )
    conn.commit()
    conn.close()

    return {
        "partnership_id": payload.partnership_id,
        "status": "ACTIVE",
        "streak_days": new_streak,
        **verdict
    }


# 5. DEMO KILL SWITCH SIMULATOR (FOR LIVE STAGE PITCH)
@app.post("/api/sprint/simulate-midnight/{partnership_id}")
def simulate_midnight(partnership_id: int, force_miss: bool = True):
    conn = get_db()
    partnership = conn.execute("SELECT * FROM partnerships WHERE id = ?", (partnership_id,)).fetchone()
    if not partnership:
        conn.close()
        raise HTTPException(status_code=404, detail="Partnership not found")

    if force_miss or partnership["user1_verified_today"] == 0:
        conn.execute(
            "UPDATE partnerships SET status = 'DISSOLVED_KILL_SWITCH', streak_days = 0 WHERE id = ?",
            (partnership_id,)
        )
        conn.commit()
        conn.close()
        return {
            "partnership_id": partnership_id,
            "status": "DISSOLVED_KILL_SWITCH",
            "streak_days": 0,
            "message": "MIDNIGHT PROTOCOL TRIGGERED: Daily proof missing. Streak wiped to 0 and partnership dissolved."
        }

    conn.close()
    return {
        "partnership_id": partnership_id,
        "status": "ACTIVE",
        "streak_days": partnership["streak_days"],
        "message": "Both partners verified before midnight. Sprint continues!"
    }

# 6. AI 14-DAY SPRINT ROADMAP GENERATOR (VAIBHAV)
from pydantic import BaseModel as _RoadmapBaseModel
from services.roadmap_agent import generate_sprint_roadmap
from services.kill_switch_agent import (
    evaluate_proof_with_agent_a5,
    get_kill_switch_status,
    init_kill_switch_tables,
)

class RoadmapRequest(_RoadmapBaseModel):
    target_role: str
    missing_skills: list[str]
    intensity_mode: str = "Standard"

@app.post("/api/roadmap/generate")
def create_sprint_roadmap(payload: RoadmapRequest):
    try:
        return generate_sprint_roadmap(
            target_role=payload.target_role,
            missing_skills=payload.missing_skills,
            intensity_mode=payload.intensity_mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class KillSwitchEvaluateRequest(BaseModel):
    partnership_id: str = "pod-alpha-1"
    user_id: str = "saurav-kumar"
    daily_task: str = "Complete daily War Room technical task"
    proof_text: str = ""
    streak_broken: bool = False


@app.on_event("startup")
def _init_kill_switch_on_startup():
    init_kill_switch_tables()


@app.post("/api/kill-switch/evaluate")
def api_kill_switch_evaluate(payload: KillSwitchEvaluateRequest):
    return evaluate_proof_with_agent_a5(
        partnership_id=payload.partnership_id,
        user_id=payload.user_id,
        daily_task=payload.daily_task,
        proof_text=payload.proof_text,
        streak_broken=payload.streak_broken,
    )


@app.get("/api/kill-switch/status/{partnership_id}")
def api_kill_switch_status(partnership_id: str, user_id: Optional[str] = None):
    status = get_kill_switch_status(partnership_id)
    if user_id and not status.get("audit_logs"):
        status["user_id"] = user_id
    return status
