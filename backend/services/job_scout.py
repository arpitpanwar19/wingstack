import os
import re
import time
import json
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
import httpx
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

BOARDS_PATH = Path(__file__).resolve().parent.parent / "data" / "company_boards.json"
_ATS_CACHE: dict = {"timestamp": 0.0, "jobs": []}
CACHE_TTL_SECONDS = 1800


def _load_company_boards() -> list[dict]:
    if not BOARDS_PATH.exists():
        return []
    try:
        return json.loads(BOARDS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _strip_html(raw: str) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", cleaned).strip()


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
    if "himalayas.app" in u:
        return "Himalayas"
    if "arbeitnow.com" in u:
        return "Arbeitnow"
    if "devpost.com" in u:
        return "Devpost Hackathon"
    if "remotive.com" in u:
        return "Remotive"
    return "Direct Career Portal"


def _is_relevant_eng_role(title: str, location: str, hubs: list[str]) -> bool:
    t = title.lower()
    eng_terms = (
        "software", "engineer", "developer", "sde", "intern", "internship",
        "backend", "frontend", "full stack", "fullstack", "systems", "infrastructure",
        "platform", "data", "ml", "ai", "security", "cloud", "devops", "site reliability",
        "sre", "mobile", "android", "ios", "compiler", "distributed", "product engineer",
        "new grad", "university", "graduate", "2026", "2027", "hackathon"
    )
    if not any(k in t for k in eng_terms):
        return False

    senior_blocks = ("director", "vp ", "vice president", "head of", "principal", "distinguished", "fellow", "staff ", "manager")
    if any(b in t for b in senior_blocks):
        return False

    loc_lower = (location or "").lower()
    india_or_remote_terms = (
        "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "noida",
        "gurugram", "gurgaon", "chennai", "delhi", "remote", "anywhere", "apac", "global"
    )
    if any(k in loc_lower for k in india_or_remote_terms):
        return True
    if not loc_lower and any("remote" in h.lower() or "india" in h.lower() for h in hubs):
        return True
    return False


async def _fetch_single_ats_board(client: httpx.AsyncClient, sem: asyncio.Semaphore, board: dict) -> list[dict]:
    api_url = board.get("api_url")
    ats_type = (board.get("ats_type") or "").lower()
    company = board.get("company", "Company")
    hubs = board.get("hq_or_india_hubs") or []
    category = board.get("category") or "Tech Company"
    if not api_url:
        return []

    async with sem:
        try:
            resp = await client.get(api_url, timeout=10.0)
            if resp.status_code != 200:
                return []
            payload = resp.json()
        except Exception:
            return []

    jobs = []
    if ats_type == "greenhouse":
        for item in payload.get("jobs", []):
            title = item.get("title", "")
            loc = (item.get("location") or {}).get("name") or ", ".join(hubs) or "India / Remote"
            if not _is_relevant_eng_role(title, loc, hubs):
                continue
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc[:80],
                "platform": f"Greenhouse ? {category}",
                "source_tier": "Direct ATS",
                "apply_url": item.get("absolute_url") or board.get("careers_page", ""),
                "posted_at": (item.get("updated_at") or "")[:10] or "Active (2026)",
                "salary_range": "",
                "description": _strip_html(item.get("content", ""))[:950],
            })
    elif ats_type == "lever":
        listings = payload if isinstance(payload, list) else payload.get("data", [])
        for item in listings:
            title = item.get("text", "")
            cats = item.get("categories") or {}
            loc = cats.get("location") or ", ".join(hubs) or "Bengaluru"
            if not _is_relevant_eng_role(title, loc, hubs):
                continue
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc[:80],
                "platform": f"Lever ? {category}",
                "source_tier": "Direct ATS",
                "apply_url": item.get("hostedUrl") or item.get("applyUrl") or board.get("careers_page", ""),
                "posted_at": "Active (2026)",
                "salary_range": "",
                "description": _strip_html(item.get("descriptionPlain") or item.get("description", ""))[:950],
            })
    elif ats_type == "ashby":
        for item in payload.get("jobs", []):
            title = item.get("title", "")
            loc = item.get("location") or ", ".join(hubs) or "Remote"
            if not _is_relevant_eng_role(title, loc, hubs):
                continue
            comp = item.get("compensationTierSummary") or ""
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc[:80],
                "platform": f"Ashby ? {category}",
                "source_tier": "Direct ATS",
                "apply_url": item.get("jobUrl") or item.get("applyUrl") or board.get("careers_page", ""),
                "posted_at": (item.get("publishedAt") or "")[:10] or "Active (2026)",
                "salary_range": comp,
                "description": _strip_html(item.get("descriptionPlain") or item.get("descriptionHtml", ""))[:950],
            })
    return jobs


async def _fetch_all_direct_ats(client: httpx.AsyncClient, boards: list[dict]) -> list[dict]:
    now = time.time()
    if _ATS_CACHE["jobs"] and (now - _ATS_CACHE["timestamp"]) < CACHE_TTL_SECONDS:
        return list(_ATS_CACHE["jobs"])

    http_boards = [b for b in boards if b.get("fetch_method") == "http_get_json" and b.get("api_url")]
    sem = asyncio.Semaphore(12)
    nested = await asyncio.gather(*[_fetch_single_ats_board(client, sem, b) for b in http_boards])
    harvested = [job for group in nested for job in group]
    if harvested:
        _ATS_CACHE["timestamp"] = now
        _ATS_CACHE["jobs"] = harvested
    return harvested


async def _fetch_custom_portals_via_tavily(
    client: httpx.AsyncClient,
    boards: list[dict],
    target_role: str,
    top_skills: list[str],
    seniority_query: str,
) -> list[dict]:
    if not TAVILY_API_KEY:
        return []

    custom_boards = [b for b in boards if b.get("fetch_method") == "custom_or_headless" and b.get("careers_page")]
    domains = []
    domain_to_company = {}
    for b in custom_boards:
        host = urlparse(b["careers_page"]).netloc.lower().replace("www.", "")
        if host:
            domains.append(host)
            domain_to_company[host] = b["company"]

    mid = max(1, len(domains) // 2)
    batches = [domains[:mid], domains[mid:]]
    skills_str = " ".join(top_skills[:3]) if top_skills else "Python C++ SQL"

    async def _query_batch(domain_slice: list[str]) -> list[dict]:
        if not domain_slice:
            return []
        try:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": f'("{target_role}" OR "Software Engineer" OR "Intern") {skills_str} ({seniority_query})',
                    "include_domains": domain_slice,
                    "search_depth": "advanced",
                    "max_results": 8,
                    "days": 30,
                    "include_answer": False,
                },
                timeout=16.0,
            )
            if resp.status_code != 200:
                return []
            out = []
            for item in resp.json().get("results", []):
                url = item.get("url", "")
                title = item.get("title", "").split("|")[0].split(" - ")[0].strip()
                if not url or not title:
                    continue
                host = urlparse(url).netloc.lower().replace("www.", "")
                comp = next((c for d, c in domain_to_company.items() if d in host), _detect_platform(url))
                out.append({
                    "title": title[:95],
                    "company": comp,
                    "location": "India / Hybrid",
                    "platform": "Custom Career Portal",
                    "source_tier": "Custom Portal",
                    "apply_url": url,
                    "posted_at": item.get("published_date") or "Active (2026)",
                    "salary_range": "",
                    "description": item.get("content", "")[:900],
                })
            return out
        except Exception:
            return []

    res = await asyncio.gather(*[_query_batch(b) for b in batches])
    return [j for grp in res for j in grp]


async def _fetch_public_remote_apis(client: httpx.AsyncClient, top_skills: list[str]) -> list[dict]:
    skill_q = top_skills[0] if top_skills else "Python"

    async def _himalayas() -> list[dict]:
        try:
            r = await client.get("https://himalayas.app/jobs/api?limit=12", timeout=10.0)
            if r.status_code != 200:
                return []
            out = []
            for j in r.json().get("jobs", []):
                title = j.get("title", "")
                if not _is_relevant_eng_role(title, "Remote", ["Remote"]):
                    continue
                min_s, max_s = j.get("minSalary"), j.get("maxSalary")
                sal = f"${int(min_s/1000)}k-${int(max_s/1000)}k" if min_s and max_s else ""
                out.append({
                    "title": title[:95],
                    "company": j.get("companyName", "Remote Startup"),
                    "location": "Remote (Global)",
                    "platform": "Himalayas",
                    "source_tier": "Remote API",
                    "apply_url": j.get("applicationLink") or j.get("guid", ""),
                    "posted_at": "Active (2026)",
                    "salary_range": sal,
                    "description": _strip_html(j.get("description", ""))[:850],
                })
            return out
        except Exception:
            return []

    async def _arbeitnow() -> list[dict]:
        try:
            r = await client.get("https://www.arbeitnow.com/api/job-board-api", timeout=10.0)
            if r.status_code != 200:
                return []
            out = []
            for j in r.json().get("data", [])[:25]:
                title = j.get("title", "")
                if not j.get("remote") or not _is_relevant_eng_role(title, "Remote", ["Remote"]):
                    continue
                out.append({
                    "title": title[:95],
                    "company": j.get("company_name", "Tech Company"),
                    "location": j.get("location") or "Remote",
                    "platform": "Arbeitnow",
                    "source_tier": "Remote API",
                    "apply_url": j.get("url", ""),
                    "posted_at": "Active (2026)",
                    "salary_range": "",
                    "description": _strip_html(j.get("description", ""))[:850],
                })
            return out[:6]
        except Exception:
            return []

    async def _remotive() -> list[dict]:
        try:
            r = await client.get(
                "https://remotive.com/api/remote-jobs",
                params={"category": "software-dev", "search": skill_q, "limit": 5},
                timeout=10.0,
            )
            if r.status_code != 200:
                return []
            return [
                {
                    "title": j.get("title", "Software Engineer")[:95],
                    "company": j.get("company_name", "Tech Company"),
                    "location": j.get("candidate_required_location", "Remote"),
                    "platform": "Remotive",
                    "source_tier": "Remote API",
                    "apply_url": j.get("url", ""),
                    "posted_at": (j.get("publication_date") or "")[:10] or "Active",
                    "salary_range": j.get("salary") or "",
                    "description": _strip_html(j.get("description", ""))[:850],
                }
                for j in r.json().get("jobs", [])[:5]
            ]
        except Exception:
            return []

    async def _devpost_hackathons() -> list[dict]:
        try:
            r = await client.get("https://devpost.com/hackathons.rss", timeout=10.0)
            if r.status_code != 200:
                return []
            root = ET.fromstring(r.text)
            out = []
            for item in root.findall(".//item")[:4]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                desc = _strip_html(item.findtext("description") or "")
                if title and link:
                    out.append({
                        "title": f"Hackathon: {title}"[:95],
                        "company": "Devpost Global",
                        "location": "Online / Global",
                        "platform": "Devpost Hackathon",
                        "source_tier": "Hackathon",
                        "apply_url": link,
                        "posted_at": "Open Registration",
                        "salary_range": "Prize Pool / Hiring",
                        "description": desc[:850],
                    })
            return out
        except Exception:
            return []

    groups = await asyncio.gather(_himalayas(), _arbeitnow(), _remotive(), _devpost_hackathons())
    return [j for g in groups for j in g]


def _local_pre_score(job: dict, flat_skills: list[str], target_role: str) -> int:
    text = f"{job.get('title', '')} {job.get('description', '')} {job.get('location', '')}".lower()
    score = 0
    if job.get("source_tier") == "Direct ATS":
        score += 25
    elif job.get("source_tier") == "Custom Portal":
        score += 18
    for kw in ("intern", "2026", "2027", "sde-1", "sde 1", "new grad", "graduate", "junior", "associate"):
        if kw in job.get("title", "").lower():
            score += 15
    for loc in ("india", "bengaluru", "bangalore", "noida", "gurugram", "hyderabad", "pune", "remote"):
        if loc in text:
            score += 10
            break
    for sk in flat_skills[:12]:
        if sk.lower() in text:
            score += 6
    for word in target_role.lower().split():
        if len(word) > 2 and word in job.get("title", "").lower():
            score += 8
    return score


def _infer_seniority_keywords(target_role: str, coding_stats: dict, resume_summary: str) -> tuple[str, str]:
    combined_text = f"{target_role} {resume_summary}".lower()
    if any(k in combined_text for k in ("intern", "internship", "student", "undergrad", "2nd year", "3rd year", "fresher", "new grad", "0-1", "entry")):
        return "intern OR fresher OR SDE-1 OR 2026 OR 2027", "Prioritize Internships, 2026/2027 New Grad, SDE-1, and Entry-Level roles. Exclude Senior/Staff/Lead/Manager roles."
    return "SDE-1 OR associate OR junior OR software engineer", "Prefer roles matching the candidate's actual experience level; penalize roles requiring 5+ years."


async def _score_jobs_with_groq(user_profile: dict, candidate_jobs: list[dict], seniority_rule: str) -> list[dict]:
    if not candidate_jobs:
        return []
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing in environment variables.")

    client = AsyncGroq(api_key=GROQ_API_KEY)
    models_resp = await client.models.list()
    all_ids = [m.id for m in models_resp.data]
    preferred = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    chosen_model = next((m for m in preferred if m in all_ids), all_ids[0])

    compact_jobs = [
        {
            "idx": i,
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "platform": j["platform"],
            "source_tier": j.get("source_tier", "Direct ATS"),
            "salary_range": j.get("salary_range", ""),
            "apply_url": j["apply_url"],
            "posted_at": j.get("posted_at", "Active (2026)"),
            "snippet": j["description"][:650],
        }
        for i, j in enumerate(candidate_jobs[:16])
    ]

    prompt = f"""
You are a precision Technical Recruiter & ATS Matching Engine.
Select and score the BEST 10 distinct openings for this candidate from the harvested ATS & career listings below.

CANDIDATE PROFILE:
- Name: {user_profile.get('full_name', 'Candidate')}
- Target Role: {user_profile.get('target_role', 'Software Engineer')}
- Preferred Location: {user_profile.get('preferred_location', 'India / Remote')}
- Verified Skills: {json.dumps(user_profile.get('verified_skills', []))}
- Resume Summary: {user_profile.get('summary', '')}

HARVESTED LISTINGS:
{json.dumps(compact_jobs, indent=2)}

RULES:
1. {seniority_rule}
2. Keep the exact `apply_url`, `company`, `platform`, and `source_tier` from the input listing.
3. Set `work_mode` to `"Remote"`, `"Hybrid"`, or `"On-site"`, and `experience_level` to `"Entry"` or `"Mid"`.
4. Extract `salary_range` if mentioned in snippet/input, else `""`.
5. Compute a realistic `match_score` (65 to 96) and write a crisp `tailored_pitch` (2-sentence recruiter outreach note) + `why_fit`.

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
      "source_tier": "Direct ATS",
      "salary_range": "string",
      "posted_at": "string",
      "apply_url": "string",
      "match_score": 91,
      "matched_skills": ["Python", "C++"],
      "missing_skills": ["Go"],
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
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.15,
        max_tokens=4096,
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

    seniority_query, seniority_rule = _infer_seniority_keywords(target_role, coding_stats, summary)
    boards = _load_company_boards()

    async with httpx.AsyncClient(headers={"User-Agent": "WingStack-ATS-Scout/2.0"}) as http_client:
        ats_jobs, custom_jobs, remote_and_hackathons = await asyncio.gather(
            _fetch_all_direct_ats(http_client, boards),
            _fetch_custom_portals_via_tavily(http_client, boards, target_role, flat_skills, seniority_query),
            _fetch_public_remote_apis(http_client, flat_skills),
        )

    seen_keys = set()
    deduped = []
    for job in ats_jobs + custom_jobs + remote_and_hackathons:
        url = (job.get("apply_url") or "").strip()
        key = (job.get("company", "").lower(), job.get("title", "").lower(), url)
        if url and key not in seen_keys:
            seen_keys.add(key)
            job["_pre_score"] = _local_pre_score(job, flat_skills, target_role)
            deduped.append(job)

    deduped.sort(key=lambda x: x.get("_pre_score", 0), reverse=True)
    return await _score_jobs_with_groq(user_profile, deduped[:18], seniority_rule)
