# 🪶 WingStack

**Turn raw GitHub commits, Codeforces ratings, and a master PDF into tailored job applications and streak-enforced peer pods.**

Most placement prep fails because you practice DSA in isolation without knowing if you're actually hireable, and then spam the same generic PDF resume across fifty portals. WingStack closes that loop: it cross-checks your resume against your real GitHub repos and Codeforces activity, matches you into a 3–4 person accountability pod stratified by consistency, swaps in relevant GitHub projects to generate company-named ATS resumes, and enforces daily progress with an automated midnight kill switch.

---

## ⚙️ How It Works

* **🧭 Signal-Backed Readiness Profiling**
  Parses your master PDF resume alongside live GitHub repositories and Codeforces stats via Groq (`llama-3.3-70b-versatile`) to flag unverified claims, calculate a readiness score, and pinpoint missing stack requirements.
* **🪢 Stratified Consistency Pods (3–4 Peers)**
  Clusters candidates targeting the same engineering role across consistency tiers—pairing one high-streak *Anchor* with *Climbers* and a *Starter*—so motivation flows downward without pairing beginners who drop off together.
* **🎯 Career Scout & GitHub-Swapped ATS Vault**
  Ranks live openings against your verified stack with direct career-page links, swaps in your most relevant GitHub projects for that specific company, and exports an ATS-scored PDF saved as `{Name}_{Company}_{Role}_Resume.pdf`.
* **⏳ Proof Audit & Midnight Kill Switch**
  Requires verifiable daily proof (commit URLs, problem submissions, or build logs). Missing a deadline triggers an automated streak reset and alerts the pod via Amazon SNS.

---

## 🧱 Tech Stack & Cloud Wiring

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Client** | React + Vite | Profile Scanner, Career Scout, ATS Resume Vault & War Room UI |
| **API & Orchestrator** | Python FastAPI + Uvicorn | Deterministic routing, tier clustering & multi-agent control loop (Railway) |
| **Inference** | Groq (`llama-3.3-70b-versatile`) | Low-latency JSON extraction, repo-to-job matching & resume rewriting |
| **Object Storage** | Amazon S3 (`wingstack-resumes`) | Master PDFs, daily proof uploads & company-tagged tailored resumes |
| **State & Memory** | Amazon DynamoDB (`wingstack-data`) | User profiles, cached GitHub repo catalogs, pod state & streak counters |
| **Alerts & Enforcement** | Amazon SNS (`wingstack-alerts`) | Pod formation broadcasts & midnight Kill Switch notifications |

---

## 🗂️ Project Layout

```text
wingstack/
├── frontend/          # React client
├── backend/           # FastAPI routes, Groq agent modules & AWS boto3 connectors
└── README.md
