import os
import io
import re
import json
import asyncio
import httpx
from pypdf import PdfReader
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()


def extract_pdf_text(pdf_bytes: bytes | None) -> str:
    """Extracts clean text from uploaded resume PDF bytes."""
    if not pdf_bytes:
        return ""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()[:8000]
    except Exception as e:
        print(f"[PDF Parse Warning] {e}")
        return ""


async def fetch_github_stats(client: httpx.AsyncClient, username: str) -> dict:
    """Fetches real public repo count, languages, and recent project descriptions."""
    if not username:
        return {"github_repos": 0, "languages": [], "top_projects": []}
    try:
        user_resp, repos_resp = await asyncio.gather(
            client.get(f"https://api.github.com/users/{username}", timeout=8.0),
            client.get(
                f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15",
                timeout=8.0,
            ),
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
        return {
            "github_repos": public_repos,
            "languages": list(languages),
            "top_projects": projects[:6],
        }
    except Exception as e:
        print(f"[GitHub Fetch Warning] {e}")
        return {"github_repos": 0, "languages": [], "top_projects": []}


async def fetch_codeforces_stats(client: httpx.AsyncClient, handle: str) -> dict:
    """Fetches Codeforces rating, rank, and solved problem count."""
    if not handle:
        return {"cf_rating": 0, "cf_rank": "unrated", "cf_solved": 0}
    try:
        info_resp, status_resp = await asyncio.gather(
            client.get(f"https://codeforces.com/api/user.info?handles={handle}", timeout=8.0),
            client.get(f"https://codeforces.com/api/user.status?handle={handle}&count=200", timeout=8.0),
        )
        rating, rank = 0, "unrated"
        if info_resp.status_code == 200 and info_resp.json().get("status") == "OK":
            user_data = info_resp.json()["result"][0]
            rating = user_data.get("rating", 0)
            rank = user_data.get("rank", "unrated")

        solved_ids = set()
        if status_resp.status_code == 200 and status_resp.json().get("status") == "OK":
            for sub in status_resp.json()["result"]:
                if sub.get("verdict") == "OK":
                    prob = sub.get("problem", {})
                    solved_ids.add(f"{prob.get('contestId')}-{prob.get('index')}")

        return {"cf_rating": rating, "cf_rank": rank, "cf_solved": len(solved_ids)}
    except Exception as e:
        print(f"[Codeforces Fetch Warning] {e}")
        return {"cf_rating": 0, "cf_rank": "unrated", "cf_solved": 0}


async def fetch_leetcode_stats(client: httpx.AsyncClient, username: str) -> dict:
    """Fetches LeetCode total solved count via public GraphQL endpoint."""
    if not username:
        return {"lc_solved": 0}
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
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
                for item in matched["submitStats"]["acSubmissionNum"]:
                    if item["difficulty"] == "All":
                        return {"lc_solved": item["count"]}
        return {"lc_solved": 0}
    except Exception as e:
        print(f"[LeetCode Fetch Warning] {e}")
        return {"lc_solved": 0}


async def fetch_gfg_stats(client: httpx.AsyncClient, handle: str) -> dict:
    """Fetches GeeksforGeeks coding score & solved problems from public profile."""
    if not handle:
        return {"gfg_solved": 0, "gfg_score": 0}
    try:
        resp = await client.get(
            f"https://www.geeksforgeeks.org/user/{handle}/",
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            timeout=8.0,
        )
        if resp.status_code == 200:
            html = resp.text
            solved_match = re.search(r'"total_problems_solved"\s*:\s*(\d+)', html)
            score_match = re.search(r'"score"\s*:\s*(\d+)', html)
            return {
                "gfg_solved": int(solved_match.group(1)) if solved_match else 0,
                "gfg_score": int(score_match.group(1)) if score_match else 0,
            }
        return {"gfg_solved": 0, "gfg_score": 0}
    except Exception as e:
        print(f"[GFG Fetch Warning] {e}")
        return {"gfg_solved": 0, "gfg_score": 0}


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
) -> dict:
    """
    Master AI Resume ATS & Multi-Source Signal Analyzer.
    Matches the exact WingStack JSON contract for POST /api/profile/analyze.
    """
    resume_text = extract_pdf_text(pdf_bytes)

    async with httpx.AsyncClient() as client:
        gh_stats, cf_stats, lc_stats, gfg_stats = await asyncio.gather(
            fetch_github_stats(client, github_username.strip()),
            fetch_codeforces_stats(client, codeforces_handle.strip()),
            fetch_leetcode_stats(client, leetcode_username.strip()),
            fetch_gfg_stats(client, gfg_handle.strip()),
        )

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")

    groq_client = AsyncGroq(api_key=api_key)

    system_prompt = """You are a senior FAANG technical recruiter and enterprise ATS scoring engine.
Analyze the candidate's resume text, GitHub activity, Codeforces rating, LeetCode stats, and GeeksforGeeks stats for their target role.
Use standard ASCII characters only. Return ONLY valid JSON matching this exact schema:
{
  "readiness_score": <integer 0-100 based on keyword depth, quantified impact, project quality, and DSA/CP proof>,
  "summary": "<2-sentence crisp executive verdict on candidate fit and top priority gap>",
  "verified_skills": {
    "languages": ["<extracted/verified programming languages>"],
    "frameworks": ["<extracted/verified frameworks & libraries>"],
    "tools_cloud": ["<extracted/verified databases, Docker, AWS, Git, cloud tools>"],
    "dsa_topics": ["<inferred algorithmic strengths from CP/LeetCode/GFG/resume>"]
  },
  "missing_keywords": ["<5-7 critical high-signal ATS keywords missing for the target role>"],
  "resume_suggestions": [
    {
      "original_bullet": "<weak or generic bullet from resume, or a project title if no PDF provided>",
      "improved_bullet": "<high-impact, quantified STAR-format ATS bullet with strong action verbs and metrics>",
      "reason": "<why this improves ATS ranking and recruiter conversion>"
    }
  ]
}"""

    user_payload = {
        "candidate_name": full_name,
        "target_role": target_role,
        "resume_text": resume_text if resume_text else "No PDF uploaded; evaluate from coding profiles.",
        "github_activity": gh_stats,
        "codeforces_activity": cf_stats,
        "leetcode_activity": lc_stats,
        "gfg_activity": gfg_stats,
    }

    completion = await groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    ai_result = json.loads(_clean_ascii(completion.choices[0].message.content))

    return {
        "user_id": user_id,
        "readiness_score": ai_result.get("readiness_score", 70),
        "summary": ai_result.get("summary", ""),
        "verified_skills": ai_result.get("verified_skills", {
            "languages": gh_stats["languages"],
            "frameworks": [],
            "tools_cloud": [],
            "dsa_topics": [],
        }),
        "missing_keywords": ai_result.get("missing_keywords", []),
        "coding_stats": {
            "github_repos": gh_stats["github_repos"],
            "cf_rating": cf_stats["cf_rating"],
            "cf_rank": cf_stats["cf_rank"],
            "lc_solved": lc_stats["lc_solved"],
            "gfg_solved": gfg_stats["gfg_solved"],
        },
        "resume_suggestions": ai_result.get("resume_suggestions", []),
    }


if __name__ == "__main__":
    async def _test():
        res = await analyze_candidate_profile(
            user_id=5,
            full_name="Arpit Panwar",
            target_role="Software Engineer",
            github_username="arpitpanwar19",
            codeforces_handle="arpitpanwar19",
            leetcode_username="arpitpanwar19",
            gfg_handle="arpitpanwar19",
        )
        print(json.dumps(res, indent=2))

    asyncio.run(_test())
