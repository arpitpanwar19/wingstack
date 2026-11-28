import os
import io
import re
import json
import asyncio
from datetime import datetime, timezone, timedelta
import httpx
from pypdf import PdfReader
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")


def extract_pdf_text(pdf_bytes: bytes | None) -> str:
    if not pdf_bytes:
        return ""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()[:9000]
    except Exception as e:
        print(f"[PDF Parse Warning] {e}")
        return ""


def _last_14_dates() -> list[str]:
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]


async def fetch_github_stats(client: httpx.AsyncClient, username: str) -> dict:
    if not username:
        return {"connected": False, "github_repos": 0, "languages": [], "top_projects": [], "daily_activity": {}}
    try:
        user_resp, repos_resp, events_resp = await asyncio.gather(
            client.get(f"https://api.github.com/users/{username}", timeout=8.0),
            client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=20", timeout=8.0),
            client.get(f"https://api.github.com/users/{username}/events/public?per_page=100", timeout=8.0),
        )
        public_repos = user_resp.json().get("public_repos", 0) if user_resp.status_code == 200 else 0
        languages = set()
        projects = []
        if repos_resp.status_code == 200:
            for repo in repos_resp.json():
                if not repo.get("fork"):
                    if repo.get("language"):
                        languages.add(repo["language"])
                    desc = repo.get("description") or ""
                    projects.append(f"{repo['name']}: {desc}"[:120])

        daily = {}
        if events_resp.status_code == 200:
            for ev in events_resp.json():
                created = (ev.get("created_at") or "")[:10]
                if created:
                    commits = len(ev.get("payload", {}).get("commits", [])) if ev.get("type") == "PushEvent" else 1
                    daily[created] = daily.get(created, 0) + max(1, commits)

        return {
            "connected": user_resp.status_code == 200,
            "github_repos": public_repos,
            "languages": list(languages),
            "top_projects": projects[:6],
            "daily_activity": daily,
        }
    except Exception:
        return {"connected": False, "github_repos": 0, "languages": [], "top_projects": [], "daily_activity": {}}


async def fetch_codeforces_stats(client: httpx.AsyncClient, handle: str) -> dict:
    if not handle:
        return {"connected": False, "cf_rating": 0, "cf_rank": "unrated", "cf_solved": 0, "daily_activity": {}}
    try:
        info_resp, status_resp = await asyncio.gather(
            client.get(f"https://codeforces.com/api/user.info?handles={handle}", timeout=8.0),
            client.get(f"https://codeforces.com/api/user.status?handle={handle}&count=250", timeout=8.0),
        )
        rating, rank, ok = 0, "unrated", False
        if info_resp.status_code == 200 and info_resp.json().get("status") == "OK":
            ok = True
            user_data = info_resp.json()["result"][0]
            rating = user_data.get("rating", 0)
            rank = user_data.get("rank", "unrated")

        solved_ids = set()
        daily = {}
        if status_resp.status_code == 200 and status_resp.json().get("status") == "OK":
            for sub in status_resp.json()["result"]:
                ts = sub.get("creationTimeSeconds")
                if ts:
                    day_str = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
                    daily[day_str] = daily.get(day_str, 0) + 1
                if sub.get("verdict") == "OK":
                    prob = sub.get("problem", {})
                    solved_ids.add(f"{prob.get('contestId')}-{prob.get('index')}")

        return {"connected": ok, "cf_rating": rating, "cf_rank": rank, "cf_solved": len(solved_ids), "daily_activity": daily}
    except Exception:
        return {"connected": False, "cf_rating": 0, "cf_rank": "unrated", "cf_solved": 0, "daily_activity": {}}


async def fetch_leetcode_stats(client: httpx.AsyncClient, username: str) -> dict:
    if not username:
        return {"connected": False, "lc_solved": 0, "daily_activity": {}}
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        submitStats { acSubmissionNum { difficulty count } }
        submissionCalendar
      }
    }
    """
    try:
        resp = await client.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": username}},
            headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
            timeout=8.0,
        )
        if resp.status_code == 200:
            matched = resp.json().get("data", {}).get("matchedUser")
            if matched:
                total = next((i["count"] for i in matched["submitStats"]["acSubmissionNum"] if i["difficulty"] == "All"), 0)
                cal_raw = matched.get("submissionCalendar") or "{}"
                cal_map = json.loads(cal_raw) if isinstance(cal_raw, str) else cal_raw
                daily = {}
                for ts_str, cnt in cal_map.items():
                    day_str = datetime.fromtimestamp(int(ts_str), tz=timezone.utc).date().isoformat()
                    daily[day_str] = daily.get(day_str, 0) + int(cnt)
                return {"connected": True, "lc_solved": total, "daily_activity": daily}
    except Exception:
        pass
    return {"connected": False, "lc_solved": 0, "daily_activity": {}}


async def fetch_gfg_stats(client: httpx.AsyncClient, handle: str) -> dict:
    if not handle:
        return {"connected": False, "gfg_solved": 0, "gfg_score": 0, "daily_activity": {}}
    try:
        resp = await client.get(
            f"https://www.geeksforgeeks.org/user/{handle}/",
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            timeout=8.0,
        )
        if resp.status_code == 200:
            solved_m = re.search(r'"total_problems_solved"\s*:\s*(\d+)', resp.text)
            score_m = re.search(r'"score"\s*:\s*(\d+)', resp.text)
            return {
                "connected": True,
                "gfg_solved": int(solved_m.group(1)) if solved_m else 0,
                "gfg_score": int(score_m.group(1)) if score_m else 0,
                "daily_activity": {},
            }
    except Exception:
        pass
    return {"connected": False, "gfg_solved": 0, "gfg_score": 0, "daily_activity": {}}


async def fetch_codechef_stats(client: httpx.AsyncClient, handle: str) -> dict:
    if not handle:
        return {"connected": False, "cc_rating": 0, "cc_stars": "", "daily_activity": {}}
    try:
        resp = await client.get(f"https://www.codechef.com/users/{handle}", headers={"User-Agent": "Mozilla/5.0"}, timeout=8.0)
        if resp.status_code == 200:
            rating_m = re.search(r'rating-number">(\d+)', resp.text)
            stars_m = re.search(r'rating-star">([^<]+)', resp.text)
            return {
                "connected": bool(rating_m),
                "cc_rating": int(rating_m.group(1)) if rating_m else 0,
                "cc_stars": stars_m.group(1).strip() if stars_m else "",
                "daily_activity": {},
            }
    except Exception:
        pass
    return {"connected": False, "cc_rating": 0, "cc_stars": "", "daily_activity": {}}


async def fetch_atcoder_stats(client: httpx.AsyncClient, handle: str) -> dict:
    if not handle:
        return {"connected": False, "ac_solved": 0, "daily_activity": {}}
    try:
        resp = await client.get(f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/ac_rank?user={handle}", timeout=8.0)
        if resp.status_code == 200:
            return {"connected": True, "ac_solved": resp.json().get("count", 0), "daily_activity": {}}
    except Exception:
        pass
    return {"connected": False, "ac_solved": 0, "daily_activity": {}}


async def fetch_hackerrank_stats(client: httpx.AsyncClient, handle: str) -> dict:
    if not handle:
        return {"connected": False, "hr_badges": 0, "daily_activity": {}}
    try:
        resp = await client.get(
            f"https://www.hackerrank.com/rest/hackers/{handle}/badges",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8.0,
        )
        if resp.status_code == 200:
            return {"connected": True, "hr_badges": len(resp.json().get("models", [])), "daily_activity": {}}
    except Exception:
        pass
    return {"connected": False, "hr_badges": 0, "daily_activity": {}}


def _clean_ascii(text: str) -> str:
    return text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")


async def analyze_candidate_profile(
    user_id: int,
    full_name: str,
    target_role: str,
    pdf_bytes: bytes | None = None,
    github_username: str = "",
    codeforces_handle: str = "",
    leetcode_username: str = "",
    gfg_handle: str = "",
    codechef_handle: str = "",
    atcoder_handle: str = "",
    hackerrank_handle: str = "",
) -> dict:
    resume_text = extract_pdf_text(pdf_bytes)

    async with httpx.AsyncClient() as client:
        gh_stats, cf_stats, lc_stats, gfg_stats, cc_stats, ac_stats, hr_stats = await asyncio.gather(
            fetch_github_stats(client, github_username.strip()),
            fetch_codeforces_stats(client, codeforces_handle.strip()),
            fetch_leetcode_stats(client, leetcode_username.strip()),
            fetch_gfg_stats(client, gfg_handle.strip()),
            fetch_codechef_stats(client, codechef_handle.strip()),
            fetch_atcoder_stats(client, atcoder_handle.strip()),
            fetch_hackerrank_stats(client, hackerrank_handle.strip()),
        )

    days = _last_14_dates()
    activity_timeline = []
    for d in days:
        gh_c = gh_stats.get("daily_activity", {}).get(d, 0)
        lc_c = lc_stats.get("daily_activity", {}).get(d, 0)
        cf_c = cf_stats.get("daily_activity", {}).get(d, 0)
        activity_timeline.append({
            "date": d,
            "label": d[5:],
            "github": gh_c,
            "leetcode": lc_c,
            "codeforces": cf_c,
            "total": gh_c + lc_c + cf_c,
        })

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")

    groq_client = AsyncGroq(api_key=api_key)
    models_resp = await groq_client.models.list()
    avail = [m.id for m in models_resp.data]
    chosen_model = next(
        (m for m in ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant"] if m in avail),
        "llama-3.3-70b-versatile",
    )

    system_prompt = """You are a senior FAANG technical recruiter and enterprise ATS scoring engine.
Analyze the candidate's resume text and live coding/developer profiles (GitHub, LeetCode, Codeforces, GFG, CodeChef, AtCoder, HackerRank) for their target role.
Return ONLY valid JSON matching this exact schema (every array MUST be non-empty):
{
  "readiness_score": 76,
  "summary": "2-sentence crisp executive verdict on candidate fit and top priority gap",
  "verified_skills_by_category": {
    "languages": ["Python", "C++"],
    "frameworks": ["FastAPI", "React"],
    "tools_cloud": ["Git", "AWS"],
    "dsa_topics": ["Dynamic Programming", "Graphs"]
  },
  "missing_skills": ["Docker", "System Design", "Kubernetes", "CI/CD", "Redis"],
  "resume_suggestions": [
    {
      "original_bullet": "weak bullet or project summary",
      "improved_bullet": "quantified STAR-format ATS bullet with metrics",
      "reason": "why this boosts recruiter conversion"
    }
  ]
}"""

    user_payload = {
        "candidate_name": full_name,
        "target_role": target_role,
        "resume_uploaded": bool(resume_text),
        "resume_text": resume_text if resume_text else "No PDF uploaded; evaluate from live coding profiles.",
        "github": gh_stats,
        "codeforces": cf_stats,
        "leetcode": lc_stats,
        "geeksforgeeks": gfg_stats,
        "codechef": cc_stats,
        "atcoder": ac_stats,
        "hackerrank": hr_stats,
    }

    completion = await groq_client.chat.completions.create(
        model=chosen_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    ai_result = json.loads(_clean_ascii(completion.choices[0].message.content))
    cat_skills = ai_result.get("verified_skills_by_category") or ai_result.get("verified_skills") or {}
    flat_verified = []
    if isinstance(cat_skills, dict):
        for v in cat_skills.values():
            if isinstance(v, list):
                flat_verified.extend([str(s) for s in v if s])
    elif isinstance(cat_skills, list):
        flat_verified = [str(s) for s in cat_skills if s]

    if not flat_verified:
        flat_verified = gh_stats.get("languages") or ["Python", "C++", "Git", "Problem Solving"]

    missing_list = ai_result.get("missing_skills") or ai_result.get("missing_keywords") or ["System Design", "Docker", "Cloud Deployment"]

    return {
        "user_id": user_id,
        "resume_parsed": bool(resume_text),
        "resume_chars": len(resume_text),
        "readiness_score": int(ai_result.get("readiness_score", 72)),
        "summary": ai_result.get("summary", ""),
        "verified_skills": list(dict.fromkeys(flat_verified)),
        "verified_skills_by_category": cat_skills if isinstance(cat_skills, dict) else {"core": flat_verified},
        "missing_skills": list(dict.fromkeys(missing_list)),
        "missing_keywords": list(dict.fromkeys(missing_list)),
        "coding_stats": {
            "github_repos": gh_stats["github_repos"],
            "github_connected": gh_stats["connected"],
            "cf_rating": cf_stats["cf_rating"],
            "cf_rank": cf_stats["cf_rank"],
            "cf_solved": cf_stats["cf_solved"],
            "lc_solved": lc_stats["lc_solved"],
            "gfg_solved": gfg_stats["gfg_solved"],
            "gfg_score": gfg_stats["gfg_score"],
            "cc_rating": cc_stats["cc_rating"],
            "cc_stars": cc_stats["cc_stars"],
            "ac_solved": ac_stats["ac_solved"],
            "hr_badges": hr_stats["hr_badges"],
        },
        "activity_timeline": activity_timeline,
        "resume_suggestions": ai_result.get("resume_suggestions", []),
    }
