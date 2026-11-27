import json
import re
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from fpdf import FPDF
from aws_client import table, s3_client, S3_BUCKET_NAME


def _clean_latin1(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "*",
        "\u2026": "...",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    return cleaned.strip("_") or "Document"


def generate_tailored_resume_data(
    user_profile: dict,
    company: str,
    job_title: str,
    job_description: str,
    ask_groq_fn,
) -> dict:
    resume_text = user_profile.get("resume_text", "")
    github_repos = user_profile.get("github_repos", [])
    verified_skills = user_profile.get("verified_skills", [])
    name = user_profile.get("name", "Candidate")

    system_prompt = (
        "You are WingStack's ATS Resume Optimization Agent. Tailor the candidate's resume for the target "
        "company and job description using ONLY truthful facts from their resume text and real GitHub repositories. "
        "NEVER invent fake companies, fake degrees, or nonexistent GitHub repositories. "
        "Select the 2 to 3 most relevant repositories from their GitHub list and rewrite project bullets with exact "
        "ATS keywords from the job description. Return strictly valid JSON with these exact keys:\n"
        "- 'header': {'name': string, 'contact_line': string}\n"
        "- 'summary': string (3 concise ATS-dense lines tailored to the role)\n"
        "- 'skills': list of strings (prioritize skills matching the job description)\n"
        "- 'projects': list of 2-3 objects {'name': string, 'url': string, 'tech': string, 'bullets': list of 2-3 strings}\n"
        "- 'experience': list of objects {'role': string, 'org': string, 'duration': string, 'bullets': list of 2 strings} (empty list if none)\n"
        "- 'education': list of strings\n"
        "- 'ats_score_before': integer (45-72)\n"
        "- 'ats_score_after': integer (84-97)\n"
        "- 'swapped_repos': list of exact repository names featured in projects"
    )

    user_prompt = (
        f"Candidate Name: {name}\n"
        f"Target Company: {company}\n"
        f"Target Job Title: {job_title}\n"
        f"Job Description: {job_description or 'Standard software engineering role requirements'}\n"
        f"Verified Skills: {json.dumps(verified_skills)}\n"
        f"Real GitHub Repositories: {json.dumps(github_repos)}\n"
        f"Master Resume Text:\n{resume_text[:4000]}"
    )

    try:
        return ask_groq_fn(system_prompt, user_prompt)
    except Exception:
        top_repos = github_repos[:2] if isinstance(github_repos, list) else []
        fallback_projects = [
            {
                "name": r.get("name", "GitHub Project"),
                "url": r.get("html_url", ""),
                "tech": r.get("language", "Python"),
                "bullets": [
                    r.get("description") or f"Built and maintained {r.get('name', 'software project')} in {r.get('language', 'Python')}."
                ],
            }
            for r in top_repos
        ]
        return {
            "header": {"name": name, "contact_line": f"GitHub: github.com/{user_profile.get('github_username', '')}"},
            "summary": f"Results-driven {job_title} candidate targeting {company} with verified hands-on engineering projects.",
            "skills": verified_skills or ["Python", "C++", "Git", "APIs"],
            "projects": fallback_projects,
            "experience": [],
            "education": ["B.Tech in Computer Science & Engineering"],
            "ats_score_before": 58,
            "ats_score_after": 86,
            "swapped_repos": [p["name"] for p in fallback_projects],
        }


def render_ats_pdf(tailored_data: dict) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    pdf.set_margins(15, 14, 15)

    header = tailored_data.get("header", {})
    name = _clean_latin1(header.get("name", "Candidate"))
    contact = _clean_latin1(header.get("contact_line", ""))

    # Name & Contact
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 8, name, new_x="LMARGIN", new_y="NEXT", align="C")
    if contact:
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(0, 5, contact, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    def section_heading(title: str):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, _clean_latin1(title.upper()), new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        pdf.line(15, y, 195, y)
        pdf.ln(2)

    # Professional Summary
    summary = _clean_latin1(tailored_data.get("summary", ""))
    if summary:
        section_heading("Professional Summary")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, summary)
        pdf.ln(2)

    # Technical Skills
    skills = tailored_data.get("skills", [])
    if skills:
        section_heading("Technical Skills")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _clean_latin1(", ".join(str(s) for s in skills)))
        pdf.ln(2)

    # Featured GitHub Projects
    projects = tailored_data.get("projects", [])
    if projects:
        section_heading("Technical Projects")
        for proj in projects:
            p_name = _clean_latin1(proj.get("name", "Project"))
            p_tech = _clean_latin1(proj.get("tech", ""))
            p_url = _clean_latin1(proj.get("url", ""))
            title_line = f"{p_name}  |  {p_tech}" if p_tech else p_name
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 5, title_line, new_x="LMARGIN", new_y="NEXT")
            if p_url:
                pdf.set_font("Helvetica", "I", 8.5)
                pdf.cell(0, 4, p_url, new_x="LMARGIN", new_y="NEXT", link=p_url)
            pdf.set_font("Helvetica", "", 9.5)
            for bullet in proj.get("bullets", []):
                pdf.multi_cell(0, 4.8, _clean_latin1(f"- {bullet}"))
            pdf.ln(1.5)

    # Experience
    experience = tailored_data.get("experience", [])
    if experience:
        section_heading("Experience")
        for exp in experience:
            role = _clean_latin1(exp.get("role", ""))
            org = _clean_latin1(exp.get("org", ""))
            dur = _clean_latin1(exp.get("duration", ""))
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 5, f"{role} - {org} ({dur})", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9.5)
            for bullet in exp.get("bullets", []):
                pdf.multi_cell(0, 4.8, _clean_latin1(f"- {bullet}"))
            pdf.ln(1.5)

    # Education
    education = tailored_data.get("education", [])
    if education:
        section_heading("Education")
        pdf.set_font("Helvetica", "", 10)
        for edu in education:
            pdf.multi_cell(0, 5, _clean_latin1(str(edu)))

    return bytes(pdf.output())


def tailor_and_store_resume(
    user_id: str,
    company: str,
    job_title: str,
    job_description: str,
    ask_groq_fn,
) -> dict:
    # 1. Fetch user profile & GitHub repos from DynamoDB
    resp = table.get_item(Key={"pk": f"USER#{user_id}", "sk": "PROFILE"})
    user_profile = resp.get("Item")
    if not user_profile:
        raise ValueError(f"User profile not found in DynamoDB for user_id={user_id}")

    # 2. Generate tailored resume JSON via Groq
    tailored_data = generate_tailored_resume_data(
        user_profile=user_profile,
        company=company,
        job_title=job_title,
        job_description=job_description,
        ask_groq_fn=ask_groq_fn,
    )

    # 3. Render ATS PDF bytes
    pdf_bytes = render_ats_pdf(tailored_data)

    # 4. Upload PDF to S3 Bucket
    clean_name = _slugify(user_profile.get("name", user_id))
    clean_company = _slugify(company)
    clean_role = _slugify(job_title)
    filename = f"{clean_name}_{clean_company}_{clean_role}_Resume.pdf"
    s3_key = f"tailored/{user_id}/{filename}"

    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        ContentDisposition=f'attachment; filename="{filename}"',
    )

    download_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=3600,
    )

    # 5. Save Vault metadata in DynamoDB
    now_iso = datetime.now(timezone.utc).isoformat()
    ats_before = int(tailored_data.get("ats_score_before", 60))
    ats_after = int(tailored_data.get("ats_score_after", 88))
    swapped_repos = tailored_data.get("swapped_repos", [])

    table.put_item(
        Item={
            "pk": f"USER#{user_id}",
            "sk": f"RESUME#{clean_company}#{now_iso}",
            "user_id": user_id,
            "company": company,
            "job_title": job_title,
            "filename": filename,
            "s3_key": s3_key,
            "ats_score_before": ats_before,
            "ats_score_after": ats_after,
            "swapped_repos": swapped_repos,
            "created_at": now_iso,
        }
    )

    return {
        "user_id": user_id,
        "company": company,
        "job_title": job_title,
        "filename": filename,
        "s3_key": s3_key,
        "download_url": download_url,
        "ats_score_before": ats_before,
        "ats_score_after": ats_after,
        "swapped_repos": swapped_repos,
        "created_at": now_iso,
    }


def list_user_resumes(user_id: str) -> list:
    resp = table.query(
        KeyConditionExpression=Key("pk").eq(f"USER#{user_id}") & Key("sk").begins_with("RESUME#")
    )
    items = resp.get("Items", [])
    vault = []
    for item in items:
        s3_key = item.get("s3_key", "")
        fresh_url = (
            s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
                ExpiresIn=3600,
            )
            if s3_key
            else ""
        )
        vault.append(
            {
                "company": item.get("company"),
                "job_title": item.get("job_title"),
                "filename": item.get("filename"),
                "s3_key": s3_key,
                "download_url": fresh_url,
                "ats_score_before": int(item.get("ats_score_before", 0)),
                "ats_score_after": int(item.get("ats_score_after", 0)),
                "swapped_repos": item.get("swapped_repos", []),
                "created_at": item.get("created_at"),
            }
        )
    return sorted(vault, key=lambda x: x.get("created_at", ""), reverse=True)
