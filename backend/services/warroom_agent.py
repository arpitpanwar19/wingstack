import os
import re
import json
import asyncio
import httpx
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


async def _call_groq_json(system_prompt: str, user_prompt: str) -> dict:
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

    kwargs = {
        "model": chosen_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.15,
        "max_tokens": 3000
    }
    if "gpt-oss" in chosen_model:
        kwargs["reasoning_effort"] = "low"

    completion = await client.chat.completions.create(**kwargs)
    raw_text = (completion.choices[0].message.content or "").strip()
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Non-JSON response from {chosen_model}: {raw_text[:300]}")
    return json.loads(raw_text[start:end + 1])


async def _inspect_real_proof(proof_url: str) -> dict:
    """
    Fetches real live metadata from GitHub API or verifies live HTTP reachability
    so fake/404 links are caught automatically.
    """
    url = (proof_url or "").strip()
    if not url:
        return {"has_url": False, "reachable": False, "evidence": "No URL provided."}

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {"User-Agent": "WingStack-WarRoom-Verifier/1.0", "Accept": "application/vnd.github+json"}

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            # 1. Specific GitHub Commit URL: github.com/{owner}/{repo}/commit/{sha}
            commit_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/commit/([^/?#]+)", url)
            if commit_match:
                owner, repo, sha = commit_match.groups()
                api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("commit", {}).get("message", "")
                    author = data.get("commit", {}).get("author", {}).get("name", owner)
                    files = [f.get("filename") for f in data.get("files", [])[:6]]
                    return {
                        "has_url": True,
                        "reachable": True,
                        "source": "GitHub Commit API",
                        "evidence": f"Verified real commit by {author}: '{msg}' | Modified files: {files}"
                    }
                return {
                    "has_url": True,
                    "reachable": False,
                    "source": "GitHub Commit API",
                    "evidence": f"GitHub commit NOT FOUND (HTTP {resp.status_code}) — invalid or private commit."
                }

            # 2. GitHub Repository URL: github.com/{owner}/{repo}
            repo_match = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", url)
            if repo_match:
                owner, repo = repo_match.groups()
                repo = repo.removesuffix(".git")
                api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                    latest = resp.json()[0]
                    msg = latest.get("commit", {}).get("message", "")
                    date = latest.get("commit", {}).get("author", {}).get("date", "")
                    return {
                        "has_url": True,
                        "reachable": True,
                        "source": "GitHub Repo API",
                        "evidence": f"Verified active repo {owner}/{repo}. Latest commit ({date}): '{msg}'"
                    }

            # 3. General Live URL (LeetCode, Codeforces, Vercel, Railway, Docs, etc.)
            resp = await client.get(url, headers=headers)
            if resp.status_code < 400:
                title_match = re.search(r"<title[^>]*>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
                page_title = re.sub(r"\s+", " ", title_match.group(1)).strip()[:120] if title_match else "Live Page"
                return {
                    "has_url": True,
                    "reachable": True,
                    "source": "Live URL Check",
                    "evidence": f"URL is live (HTTP {resp.status_code}) | Page title: '{page_title}'"
                }
            return {
                "has_url": True,
                "reachable": False,
                "source": "Live URL Check",
                "evidence": f"Broken/inaccessible URL (HTTP {resp.status_code})."
            }
    except Exception as exc:
        return {
            "has_url": True,
            "reachable": False,
            "source": "Network Check",
            "evidence": f"URL could not be reached: {type(exc).__name__}"
        }


async def match_warroom_partner(
    current_user: dict,
    candidate_partners: list[dict],
    intensity_mode: str = "Grind"
) -> dict:
    """
    Matches a user with the highest-compatibility accountability partner from DB
    and generates a shared 7-day War Room sprint goal.
    """
    valid_candidates = [
        c for c in candidate_partners
        if c.get("user_id") != current_user.get("user_id")
    ]

    if not valid_candidates:
        return {
            "matched": False,
            "partner_id": None,
            "partner_name": "Solo Sprint Mode",
            "partner_role": "Self-Paced",
            "partner_handles": {},
            "compatibility_score": 100,
            "match_reason": "Running in Solo War Room mode — AI Judge verifies all your daily commits and DSA logs.",
            "shared_sprint_goal": f"Complete 14 DSA problems and 1 deployed feature in {intensity_mode} mode.",
            "daily_checkpoint": "Push 1 GitHub commit or solve 2 medium DSA problems daily."
        }

    compact_candidates = [
        {
            "user_id": c.get("user_id"),
            "full_name": c.get("full_name") or c.get("name") or "WingStack Builder",
            "target_role": c.get("target_role", "Software Engineer"),
            "skills": c.get("verified_skills", [])[:8],
            "coding_stats": c.get("coding_stats", {}),
            "handles": c.get("handles", {})
        }
        for c in valid_candidates[:10]
    ]

    prompt = f"""
You are the WingStack War Room Matchmaker AI.
Pair the Current User with the SINGLE best accountability partner from the Candidate Pool based on target role overlap, complementary tech stack, coding intensity, and "{intensity_mode}" mode.

CURRENT USER:
{json.dumps({
    "user_id": current_user.get("user_id"),
    "full_name": current_user.get("full_name") or current_user.get("name") or "User",
    "target_role": current_user.get("target_role", "Software Engineer"),
    "skills": current_user.get("verified_skills", [])[:8],
    "coding_stats": current_user.get("coding_stats", {})
}, indent=2)}

CANDIDATE POOL:
{json.dumps(compact_candidates, indent=2)}

Return ONLY raw valid JSON with this exact schema:
{{
  "selected_partner_id": "string",
  "compatibility_score": 91,
  "match_reason": "1 crisp sentence explaining why their roles, stacks, and coding pace fit.",
  "shared_sprint_goal": "1 concrete, measurable 7-day goal tailored to both users and {intensity_mode} mode.",
  "daily_checkpoint": "1 specific daily proof requirement each member must submit every 24h."
}}
"""

    ai_result = await _call_groq_json(
        "You are a War Room Matchmaker JSON API. Output ONLY raw valid JSON starting with { and ending with }.",
        prompt
    )

    selected_id = ai_result.get("selected_partner_id")
    chosen_partner = next(
        (c for c in valid_candidates if str(c.get("user_id")) == str(selected_id)),
        valid_candidates[0]
    )

    return {
        "matched": True,
        "partner_id": chosen_partner.get("user_id"),
        "partner_name": chosen_partner.get("full_name") or chosen_partner.get("name") or "WingStack Builder",
        "partner_role": chosen_partner.get("target_role", "Software Engineer"),
        "partner_handles": chosen_partner.get("handles", {}),
        "compatibility_score": int(ai_result.get("compatibility_score", 85)),
        "match_reason": ai_result.get("match_reason", "Strong alignment in target engineering role and sprint pace."),
        "shared_sprint_goal": ai_result.get("shared_sprint_goal", "Ship 1 backend project & solve 15 DSA problems in 7 days."),
        "daily_checkpoint": ai_result.get("daily_checkpoint", "Submit a GitHub commit URL or LeetCode/CF submission link daily.")
    }


async def verify_daily_proof(
    sprint_goal: str,
    daily_checkpoint: str,
    proof_url: str,
    proof_note: str,
    current_streak: int = 0,
    user_name: str = "Builder"
) -> dict:
    """
    Universal AI Judge for ANY user on the platform (solo, paired, or squad).
    Inspects the real live proof URL first, then evaluates work quality with Groq.
    """
    clean_url = (proof_url or "").strip()
    clean_note = (proof_note or "").strip()

    if not clean_url and len(clean_note) < 15:
        return {
            "user_name": user_name,
            "verified": False,
            "confidence": 99,
            "live_evidence": "No proof link or detailed summary submitted.",
            "ai_feedback": "Submission rejected: attach a real GitHub commit/repo, coding submission link, or a concrete technical summary.",
            "updated_streak": current_streak
        }

    inspection = await _inspect_real_proof(clean_url)

    # Hard reject broken/fake URLs immediately
    if inspection["has_url"] and not inspection["reachable"]:
        return {
            "user_name": user_name,
            "verified": False,
            "confidence": 98,
            "live_evidence": inspection["evidence"],
            "ai_feedback": f"Rejected: your proof link could not be verified ({inspection['evidence']}). Submit a valid public URL.",
            "updated_streak": current_streak
        }

    prompt = f"""
You are the WingStack Universal Work Verification AI.
Verify whether {user_name}'s submitted proof demonstrates genuine daily engineering/DSA work toward their goal.

USER: {user_name}
SPRINT GOAL: {sprint_goal}
DAILY CHECKPOINT: {daily_checkpoint}
SUBMITTED URL: {clean_url or "None"}
LIVE INSPECTED EVIDENCE: {inspection["evidence"]}
SUBMITTED WORK NOTE: {clean_note or "None"}

RULES:
1. Approve (`"verified": true`) if the live inspected evidence or detailed work note confirms real coding, problem-solving, deployment, or study work aligned with their goal.
2. Reject (`"verified": false`) if the link is a generic homepage (e.g. google.com, example.com) with no real work evidence, or the note is empty/vague spam.
3. Write 1 sharp, specific sentence of `ai_feedback` referencing what was actually found in their commit/link/note.

Return ONLY raw valid JSON:
{{
  "verified": true,
  "confidence": 95,
  "ai_feedback": "string"
}}
"""

    ai_result = await _call_groq_json(
        "You are a Work Verification JSON API. Output ONLY raw valid JSON starting with { and ending with }.",
        prompt
    )

    is_verified = bool(ai_result.get("verified", False))
    new_streak = (current_streak + 1) if is_verified else current_streak

    return {
        "user_name": user_name,
        "verified": is_verified,
        "confidence": int(ai_result.get("confidence", 85)),
        "live_evidence": inspection["evidence"],
        "ai_feedback": ai_result.get("ai_feedback", "Submission evaluated."),
        "updated_streak": new_streak
    }


async def verify_room_all_members(members_submissions: list[dict]) -> dict:
    """
    Verifies EVERY member's daily work in a War Room / Team Sprint in parallel.
    Each item in members_submissions:
      {
        "user_id": str,
        "user_name": str,
        "sprint_goal": str,
        "daily_checkpoint": str,
        "proof_url": str,
        "proof_note": str,
        "current_streak": int
      }
    """
    if not members_submissions:
        return {"total_members": 0, "verified_count": 0, "all_verified": False, "results": []}

    tasks = [
        verify_daily_proof(
            sprint_goal=m.get("sprint_goal", ""),
            daily_checkpoint=m.get("daily_checkpoint", ""),
            proof_url=m.get("proof_url", ""),
            proof_note=m.get("proof_note", ""),
            current_streak=int(m.get("current_streak", 0)),
            user_name=m.get("user_name", "Builder")
        )
        for m in members_submissions
    ]
    verdicts = await asyncio.gather(*tasks)

    enriched = []
    for member, verdict in zip(members_submissions, verdicts):
        enriched.append({"user_id": member.get("user_id"), **verdict})

    verified_count = sum(1 for r in enriched if r["verified"])
    return {
        "total_members": len(enriched),
        "verified_count": verified_count,
        "pending_count": len(enriched) - verified_count,
        "all_verified": verified_count == len(enriched),
        "results": enriched
    }


if __name__ == "__main__":
    async def _smoke_test():
        print("--- TESTING UNIVERSAL WORK VERIFICATION ACROSS ALL USERS ---")
        squad = [
            {
                "user_id": "u_arpit",
                "user_name": "Arpit Panwar",
                "sprint_goal": "Build WingStack AI agents",
                "daily_checkpoint": "Push working backend service code to GitHub",
                "proof_url": "https://github.com/fastapi/fastapi",
                "proof_note": "Added async job scout and War Room verifier endpoints.",
                "current_streak": 6
            },
            {
                "user_id": "u_saurav",
                "user_name": "Saurav Kumar",
                "sprint_goal": "Build WingStack AI agents",
                "daily_checkpoint": "Push working backend service code to GitHub",
                "proof_url": "https://github.com/fastapi/fastapi/commit/nonexistentfakehash123",
                "proof_note": "Finished everything bro",
                "current_streak": 4
            }
        ]
        room_report = await verify_room_all_members(squad)
        print(json.dumps(room_report, indent=2))

    asyncio.run(_smoke_test())

