import os
import json
import asyncio
import httpx
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def _detect_platform(url: str) -> str:
    u = url.lower()
    if "greenhouse.io" in u:
        return "Greenhouse ATS"
    if "lever.co" in u:
        return "Lever ATS"
    if "ashbyhq.com" in u:
        return "Ashby ATS"
    if "workatastartup.com" in u:
        return "YC Work at a Startup"
    if "wellfound.com" in u or "angel.co" in u:
        return "Wellfound"
    if "unstop.com" in u:
        return "Unstop"
    if "cuvette.tech" in u:
        return "Cuvette"
    if "instahyre.com" in u:
        return "Instahyre"
    if "cutshort.io" in u:
        return "Cutshort"
    if "internshala.com" in u:
        return "Internshala"
    if "naukri.com" in u:
        return "Naukri"
    if "linkedin.com" in u:
        return "LinkedIn"
    if "remotive.com" in u:
        return "Remotive"
    return "Direct Career Portal"


def _is_individual_job_url(url: str, title: str = "") -> bool:
    u = url.lower().rstrip("/")
    t = title.lower()
    if any(k in t for k in ("000+ ", "jobs in india", "jobs in bengaluru", "jobs in delhi", "jobs in remote", "top 10", "salaries")):
        return False
    bad_patterns = (
        "naukri.com/fastapi-jobs",
        "-jobs-in-",
        "/internships/python-internship",
        "/internships/software-development-internship",
        "/developers?skillnames",
        "/jobs/search",
        "linkedin.com/jobs/software-engineer-jobs",
        "linkedin.com/jobs/c++-developer-jobs",
        "linkedin.com/jobs/python-developer-jobs",
    )
    if any(p in u for p in bad_patterns):
        return False
    if "linkedin.com/jobs/" in u and "/view/" not in u:
        return False
    if "naukri.com/" in u and "job-listings-" not in u:
        return False
    if "internshala.com/" in u and "/internship/detail/" not in u and "/job/detail/" not in u:
        return False
    return True


def _infer_seniority_keywords(target_role: str, coding_stats: dict, resume_summary: str) -> tuple[str, str]:
    combined_text = f"{target_role} {resume_summary}".lower()
    if any(k in combined_text for k in ("intern", "internship", "student", "undergrad", "2nd year", "3rd year", "fresher", "new grad", "0-1", "entry")):
        return "intern OR fresher OR SDE-1 OR entry level 2026", "EXCLUDE Senior, Staff, Lead, Principal, Manager, Director, or 3+ years experience roles."
    return "SDE-1 OR associate OR junior OR software engineer 2026", "Prefer roles matching the candidate's actual experience level; penalize roles requiring 5+ years."


async def _fetch_tavily_jobs(
    client: httpx.AsyncClient,
    target_role: str,
    top_skills: list[str],
    seniority_query: str,
    location_pref: str
) -> list[dict]:
    if not TAVILY_API_KEY:
        return []

    skills_str = " ".join(top_skills[:4]) if top_skills else "Python C++ SQL"
    loc = location_pref or "India"

    buckets = [
        {
            "query": f'"{target_role}" {skills_str} ({seniority_query})',
            "domains": [
                "boards.greenhouse.io", "job-boards.greenhouse.io", "jobs.lever.co",
                "jobs.ashbyhq.com", "workatastartup.com", "wellfound.com"
            ],
            "max_results": 8,
            "days": 30
        },
        {
            "query": f'{target_role} {skills_str} {loc} ({seniority_query})',
            "domains": [
                "unstop.com", "cuvette.tech", "instahyre.com", "cutshort.io",
                "internshala.com", "naukri.com"
            ],
            "max_results": 8,
            "days": 21
        },
        {
            "query": f'"{target_role}" {skills_str} {loc} hiring 2026',
            "domains": ["linkedin.com", "amazon.jobs", "careers.google.com", "careers.microsoft.com"],
            "max_results": 5,
            "days": 21
        }
    ]

    async def _run_bucket(b: dict) -> list[dict]:
        try:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": b["query"],
                    "include_domains": b["domains"],
                    "search_depth": "advanced",
                    "max_results": b["max_results"],
                    "days": b["days"],
                    "include_answer": False
                },
                timeout=18.0
            )
            if resp.status_code != 200:
                return []
            items = []
            for item in resp.json().get("results", []):
                url = item.get("url", "")
                title = item.get("title", "").split("|")[0].strip()
                if not url or not title or not _is_individual_job_url(url, title):
                    continue
                snippet = item.get("content", "")
                plat = _detect_platform(url)
                items.append({
                    "title": title[:95],
                    "company": plat,
                    "location": loc,
                    "platform": plat,
                    "apply_url": url,
                    "posted_at": item.get("published_date") or "Recent (2026)",
                    "description": snippet[:950]
                })
            return items
        except Exception:
            return []

    results_per_bucket = await asyncio.gather(*[_run_bucket(b) for b in buckets])
    return [job for group in results_per_bucket for job in group]


async def _fetch_remotive_jobs(client: httpx.AsyncClient, target_role: str, top_skills: list[str]) -> list[dict]:
    search_term = top_skills[0] if top_skills else "Python"
    try:
        resp = await client.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev", "search": search_term, "limit": 6},
            timeout=12.0
        )
        if resp.status_code != 200:
            return []
        jobs = []
        for j in resp.json().get("jobs", [])[:6]:
            jobs.append({
                "title": j.get("title", "Software Engineer"),
                "company": j.get("company_name", "Tech Company"),
                "location": j.get("candidate_required_location", "Remote"),
                "platform": "Remotive",
                "apply_url": j.get("url", ""),
                "posted_at": (j.get("publication_date") or "")[:10] or "Recent",
                "description": (j.get("description", "") or "")[:950]
            })
        return jobs
    except Exception:
        return []


async def _score_jobs_with_groq(user_profile: dict, candidate_jobs: list[dict], seniority_rule: str) -> list[dict]:
    if not candidate_jobs:
        return []

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing in environment variables.")

    client = AsyncGroq(api_key=GROQ_API_KEY)
    models_resp = await client.models.list()
    all_ids = [m.id for m in models_resp.data]
    preferred = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]
    chosen_model = next((m for m in preferred if m in all_ids), "llama-3.3-70b-versatile")

    compact_jobs = [
        {
            "idx": i,
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "platform": j["platform"],
            "apply_url": j["apply_url"],
            "posted_at": j.get("posted_at", "Recent"),
            "snippet": j["description"][:700]
        }
        for i, j in enumerate(candidate_jobs[:18])
    ]

    prompt = f"""
You are a precision Technical Recruiter & ATS Matching Engine.
Match genuine, active, level-appropriate software/internship openings to this user's profile. Return UP TO 10 distinct matched jobs.

REAL USER PLATFORM PROFILE:
- Name: {user_profile.get('full_name', 'Candidate')}
- Target Role: {user_profile.get('target_role', 'Software Engineer')}
- Preferred Location: {user_profile.get('preferred_location', 'India / Remote')}
- Verified Skills: {json.dumps(user_profile.get('verified_skills', []))}
- Resume Summary: {user_profile.get('summary', '')}

CANDIDATE LISTINGS:
{json.dumps(compact_jobs, indent=2)}

RULES:
1. {seniority_rule}
2. Drop any generic search-index pages (like "28,000+ jobs") or non-software roles.
3. Extract the real hiring company name from title/snippet/URL.
4. Set `work_mode` to one of `"Remote"`, `"Hybrid"`, or `"On-site"`, and `experience_level` to `"Entry"` or `"Mid"`.
5. Compute a distinct ATS `match_score` (62 to 96) and write a crisp `tailored_pitch` (outreach message) + `why_fit`.

Return ONLY raw valid JSON:
{{
  "matched_jobs": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "work_mode": "Remote",
      "experience_level": "Entry",
      "platform": "string",
      "posted_at": "string",
      "apply_url": "string",
      "match_score": 89,
      "matched_skills": ["Python", "FastAPI"],
      "missing_skills": ["Docker"],
      "why_fit": "string",
      "tailored_pitch": "string"
    }}
  ]
}}
"""

    completion = await client.chat.completions.create(
        model=chosen_model,
        messages=[
            {"role": "system", "content": "You are a precision ATS JSON API. Output ONLY raw valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.15,
        max_tokens=4096
    )

    parsed = json.loads(completion.choices[0].message.content)
    jobs = parsed.get("matched_jobs", [])
    for j in jobs:
        j["match_percentage"] = j.get("match_score", 80)
    jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return jobs


async def find_and_score_jobs(user_profile: dict) -> list[dict]:
    raw_skills = user_profile.get("verified_skills", [])
    if isinstance(raw_skills, dict):
        flat_skills = [s for v in raw_skills.values() if isinstance(v, list) for s in v]
    else:
        flat_skills = list(raw_skills)

    target_role = user_profile.get("target_role") or "Software Engineer"
    summary = user_profile.get("summary") or ""
    coding_stats = user_profile.get("coding_stats") or {}
    location_pref = user_profile.get("preferred_location") or "India"

    seniority_query, seniority_rule = _infer_seniority_keywords(target_role, coding_stats, summary)

    async with httpx.AsyncClient() as http_client:
        tavily_jobs, remotive_jobs = await asyncio.gather(
            _fetch_tavily_jobs(http_client, target_role, flat_skills, seniority_query, location_pref),
            _fetch_remotive_jobs(http_client, target_role, flat_skills)
        )

    seen_urls = set()
    combined = []
    for job in tavily_jobs + remotive_jobs:
        url = job.get("apply_url", "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined.append(job)

    return await _score_jobs_with_groq(user_profile, combined, seniority_rule)
