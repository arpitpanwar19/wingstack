# 🪶 WingStack
 **AI Career Telemetry, Direct ATS Scout & Accountability Engine**

**WingStack** turns fragmented student coding proof into verified job matches and enforced daily execution. Built for CS students preparing for internships and placements, it unifies live coding activity across 7 platforms, harvests openings directly from **155 curated tech company career portals**, stores candidate credentials in an **AWS DynamoDB + S3 Vault**, and enforces daily shipping through a **War Room Midnight Kill Switch**.

---

## ✨ Core Architecture & Engines

### 🔐 1. AWS Candidate Vault (`DynamoDB` + `S3`)
- **Read-Only Locked Identity:** Profiles lock automatically after verification to prevent accidental drift across ATS and job-matching pipelines, with a dedicated **Edit Profile & Connectors** mode for intentional updates.
- **AWS S3 Resume Storage (`wingstack-resumes`):** Stores candidate resume PDFs with time-limited presigned URLs for secure one-click viewing.
- **AWS DynamoDB Persistence (`wingstack-data`):** Syncs candidate metadata, readiness scores, and all 7 competitive/developer platform connectors (`GitHub`, `LeetCode`, `Codeforces`, `GeeksforGeeks`, `CodeChef`, `AtCoder`, `HackerRank`).

### 📊 2. 7-Arena Live Telemetry & ATS Analyzer
- Queries live stats across **GitHub**, **LeetCode**, **Codeforces**, **GFG**, **CodeChef**, **AtCoder**, and **HackerRank** alongside PDF resume parsing (`pypdf`).
- Generates a **14-day multi-platform activity graph**, identifies missing role-specific skills, rewrites resume bullets into quantified STAR format, and generates a tailored **14-Day AI Sprint Roadmap**.

### 🎯 3. 155-Company Direct ATS Career Scout & Resume Tailor
- **Zero Aggregator Spam:** Harvests live engineering & internship openings directly from **155 curated Indian & global tech companies** across **Greenhouse**, **Lever**, **Ashby**, **Workday CXS**, and custom company career portals.
- **Pre-Scoring & Live Link Verification:** Filters for India / Remote-India early-career roles, verifies live HTTP 200 endpoints, and provides **1-click Resume Tailoring** + cold recruiter outreach drafts per role.

### ⚡ 4. The War Room & Midnight Kill Switch
- Pairs two students with matching target roles and intensity modes (`Hell Mode`, `Normal Mode`, `Chill Mode`).
- **API-Verified Proof of Work:** Inspects submitted GitHub commit URLs via the GitHub API to verify real code was shipped.
- **Midnight Protocol:** Missing a daily checkpoint before midnight wipes the shared streak to `0` and dissolves the partnership.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React, Vite, Tailwind CSS, Lucide Icons, Axios (Deployed on Vercel) |
| **Backend** | FastAPI, Python, Uvicorn, `httpx`, `pypdf` (Deployed on Railway) |
| **AI & Inference** | Groq LLM API (`llama-3.3-70b-versatile` / `gpt-oss-120b`), Tavily Search API |
| **Cloud & Storage** | AWS DynamoDB (`wingstack-data`), AWS S3 (`wingstack-resumes`), SQLite fallback |
| **Live Data APIs** | Greenhouse, Lever, Ashby, Workday CXS, GitHub REST, LeetCode GraphQL, Codeforces API |
