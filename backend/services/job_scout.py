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
    if "wellfound.com" in u or "angel.co" in u:
        return "Wellfound"
    if "internshala.com" in u:
        return "Internshala"
    if "naukri.com" in u:
        return "Naukri"
    if "remote.co" in u:
        return "Remote.co"
    if "linkedin.com" in u:
        return "LinkedIn"
    if "remotive.com" in u:
        return "Remotive"
    return "Career Page"


def _is_individual_job_url(url: str) -> bool:
    """Filter out generic search/category directory pages so only actual job listings pass."""
    u = url.lower().rstrip("/")
    bad_patterns = (
        "naukri.com/fastapi-jobs",
        "-jobs-in-",
        "/internships/python-internship",
        "/internships/software-development-internship",
        "/developers?skillnames",
        "/jobs/search",
    )
    if any(p in u for p in bad_patterns):
        return False
    if "naukri.com/" in u and "job-listings-" not in u:
        return False
    if "internshala.com/" in u and "/internship/detail/" not in u and "/job/detail/" not in u:
        return False
    return True


def _infer_seniority_keywords(target_role: str, coding_stats: dict, resume_summary: str) -> tuple[str, str]:
    """Infer whether user is Intern/Fresher vs Mid/Senior from real platform profile."""
    combined_text = f"{target_role} {resume_summary}".lower()
    if any(k in combined_text for k in ("intern", "internship", "student", "undergrad", "2nd year", "3rd year", "fresher", "new grad", "0-1", "entry")):
        return "intern OR fresher OR entry level", "EXCLUDE Senior, Staff, Lead, Principal, Manager, Director, or 3+ years experience roles."
    if any(k in combined_text for k in ("senior", "staff", "lead", "principal", "5+ years")):
        return "senior OR lead", "Focus on mid-to-senior engineering roles matching their experience."
    return "junior OR associate OR entry level OR software engineer", "Prefer roles matching the candidate's actual experience level; penalize roles requiring 5+ years."


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
                "jobs.ashbyhq.com", "myworkdayjobs.com", "careers.smartrecruiters.com",
                "amazon.jobs", "careers.google.com", "careers.microsoft.com"
            ],
            "max_results": 6
        },
        {
            "query": f'"{target_role}" {skills_str} {loc} ({seniority_query})',
            "domains": ["naukri.com", "internshala.com"],
            "max_results": 5
        },
        {
            "query": f'"{target_role}" {skills_str} ({seniority_query})',
            "domains": ["wellfound.com", "remote.co"],
            "max_results": 5
        },
        {
            "query": f'"{target_role}" {skills_str} {loc} ({seniority_query})',
            "domains": ["linkedin.com"],
            "max_results": 4
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
                    "include_answer": False
                },
                timeout=18.0
            )
            if resp.status_code != 200:
                return []
            items = []
            for item in resp.json().get("results", []):
                url = item.get("url", "")
                if not url or not _is_individual_job_url(url):
                    continue
                title = item.get("title", "").split("|")[0].strip()
                snippet = item.get("content", "")
                if title:
                    plat = _detect_platform(url)
                    items.append({
                        "title": title[:95],
                        "company": plat,
                        "location": loc,
                        "platform": plat,
                        "apply_url": url,
                        "description": snippet[:950]
                    })
            return items
        except Exception:
            return []

    results_per_bucket = await asyncio.gather(*[_run_bucket(b) for b in buckets])
    return [job for group in results_per_bucket for job in group]


async def _fetch_remotive_jobs(client: httpx.AsyncClient, target_role: str, top_skills: list[str]) -> list[dict]:
    search_term = top_skills[0] if top_skills else target_role
    try:
        resp = await client.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev", "search": search_term, "limit": 5},
            timeout=12.0
        )
        if resp.status_code != 200:
            return []
        jobs = []
        for j in resp.json().get("jobs", [])[:5]:
            jobs.append({
                "title": j.get("title", "Software Engineer"),
                "company": j.get("company_name", "Tech Company"),
                "location": j.get("candidate_required_location", "Remote"),
                "platform": "Remotive",
                "apply_url": j.get("url", ""),
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
    allowed_prefixes = ("llama-", "meta-llama/", "gemma", "mixtral", "openai/gpt-oss")
    blocked = ("guard", "whisper", "tts")
    available = [m for m in all_ids if m.lower().startswith(allowed_prefixes) and not any(b in m.lower() for b in blocked)]
    preferred = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "allam-2-7b"
    ]
    chosen_model = next((m for m in preferred if m in available), "allam-2-7b")

    compact_jobs = [
        {
            "idx": i,
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "platform": j["platform"],
            "apply_url": j["apply_url"],
            "snippet": j["description"][:700]
        }
        for i, j in enumerate(candidate_jobs[:15])
    ]

    prompt = f"""
You are a precision Technical Recruiter & ATS Matching Engine.
Match ONLY genuine, level-appropriate openings to this exact user's live platform profile.

REAL USER PLATFORM PROFILE:
- Name: {user_profile.get('full_name', 'Candidate')}
- Target Role: {user_profile.get('target_role', 'Software Engineer')}
- Preferred Location: {user_profile.get('preferred_location', 'India / Remote')}
- Verified Resume & Repo Skills: {json.dumps(user_profile.get('verified_skills', []))}
- Live Coding Stats (GitHub/CF/LC/GFG): {json.dumps(user_profile.get('coding_stats', {}))}
- Top GitHub Projects / Domains: {json.dumps(user_profile.get('github_top_repos', []))}
- Resume Summary: {user_profile.get('summary', '')}

CANDIDATE LISTINGS:
{json.dumps(compact_jobs, indent=2)}

STRICT MATCHING RULES:
1. {seniority_rule} Drop mismatched seniority roles completely.
2. Drop any non-engineering roles or generic job-search directory pages.
3. Extract the actual hiring company name from the title/snippet/URL.
4. Compute an honest, distinct ATS `match_score` (50 to 97) comparing the user's real skills, GitHub projects, and DSA/CP ratings against each job's requirements.
5. `matched_skills`: exact skills from the user's profile that match this job (max 5).
6. `missing_skills`: exact skills required by THIS job that are missing from the user's profile (max 4).
7. `why_fit`: 1 specific sentence citing the user's actual skills/projects/CP stats and how they align with this role.

Return ONLY raw valid JSON:
{{
  "matched_jobs": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "platform": "string",
      "apply_url": "string",
      "match_score": 89,
      "matched_skills": ["Python", "FastAPI"],
      "missing_skills": ["Docker"],
      "why_fit": "string"
    }}
  ]
}}
"""

    kwargs = {
        "model": chosen_model,
        "messages": [
            {"role": "system", "content": "You are a precision ATS JSON API. Output ONLY raw valid JSON starting with { and ending with }."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.15,
        "max_tokens": 4096
    }
    if "gpt-oss" in chosen_model:
        kwargs["reasoning_effort"] = "low"

    completion = await client.chat.completions.create(**kwargs)
    raw_text = (completion.choices[0].message.content or "").strip()
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Non-JSON response from {chosen_model}: {raw_text[:300]}")

    parsed = json.loads(raw_text[start:end + 1])
    jobs = parsed.get("matched_jobs", [])
    jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return jobs


async def find_and_score_jobs(user_profile: dict) -> list[dict]:
    """
    Main entrypoint wired to live user profile in DB.
    Accepts real user record fields from Resume Analyzer + Profile DB:
      - full_name, target_role, preferred_location
      - verified_skills (list[str] or categorized dict)
      - coding_stats (github_repos, cf_rating, lc_solved, gfg_solved)
      - github_top_repos (list[str])
      - summary (str)
    """
    raw_skills = user_profile.get("verified_skills", [])
    if isinstance(raw_skills, dict):
        flat_skills = []
        for v in raw_skills.values():
            if isinstance(v, list):
                flat_skills.extend(v)
    else:
        flat_skills = list(raw_skills)

    target_role = user_profile.get("target_role") or "Software Engineer"
    summary = user_profile.get("summary") or ""
    coding_stats = user_profile.get("coding_stats") or {}
    location_pref = user_profile.get("preferred_location") or "India"

    seniority_query, seniority_rule = _infer_seniority_keywords(target_role, coding_stats, summary)

    async with httpx.AsyncClient() as http_client:
        tavily_task = _fetch_tavily_jobs(http_client, target_role, flat_skills, seniority_query, location_pref)
        remotive_task = _fetch_remotive_jobs(http_client, target_role, flat_skills)
        tavily_jobs, remotive_jobs = await asyncio.gather(tavily_task, remotive_task)

    seen_urls = set()
    combined = []
    for job in tavily_jobs + remotive_jobs:
        url = job.get("apply_url", "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined.append(job)

    return await _score_jobs_with_groq(user_profile, combined, seniority_rule)


if __name__ == "__main__":
    # Standalone smoke test (in production, backend/main.py passes the live DB user profile here)
    test_db_user = {
        "full_name": "Arpit Panwar",
        "target_role": "Software Engineer Intern",
        "preferred_location": "India / Remote",
        "verified_skills": ["Python", "C++", "FastAPI", "AWS DynamoDB", "AWS S3", "Data Structures", "Algorithms"],
        "coding_stats": {"github_repos": 15, "cf_rating": 1250, "lc_solved": 220, "gfg_solved": 150},
        "github_top_repos": ["wingstack (AI career & ATS backend in Python/AWS)", "InfraPulse (IoT ESP32 structural monitoring)"],
        "summary": "2nd-year B.Tech CSE student focused on backend APIs in Python/FastAPI, AWS cloud services, and C++ competitive programming."
    }
    results = asyncio.run(find_and_score_jobs(test_db_user))
    print(json.dumps(results, indent=2))
