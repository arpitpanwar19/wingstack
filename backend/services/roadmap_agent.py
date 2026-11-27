import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def get_best_groq_model(client: Groq) -> str:
    """Fetches currently active models for this API key and picks the best available one."""
    env_model = os.getenv("GROQ_MODEL")
    if env_model:
        return env_model

    models = client.models.list().data
    active_ids = [
        m.id for m in models
        if not any(skip in m.id.lower() for skip in ["whisper", "guard", "tts", "vision", "embed"])
    ]

    preferred_order = [
        "llama-3.3-70b",
        "llama-3.1-70b",
        "meta-llama/llama-4",
        "qwen",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.1-8b",
    ]
    for pref in preferred_order:
        for model_id in active_ids:
            if pref in model_id.lower():
                return model_id

    if not active_ids:
        raise RuntimeError("No active chat models available on this Groq API key.")
    return active_ids[0]


def generate_sprint_roadmap(target_role: str, missing_skills: list[str], intensity_mode: str = "Standard") -> dict:
    """
    Vaibhav's AI Agent: Generates a personalized 14-day upskilling sprint
    and recommended capstone mini-project to close the user's missing skills.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing in environment variables.")

    client = Groq(api_key=api_key)
    model_name = get_best_groq_model(client)

    skills_str = ", ".join(missing_skills) if missing_skills else "System Design, Docker, Cloud Deployment"

    system_prompt = (
        "You are an expert technical career mentor. Generate a practical, concrete 14-day upskilling sprint "
        "and a resume-worthy mini-project to help the candidate master their missing skills for their target role. "
        "You must respond strictly in valid JSON matching this exact schema:\n"
        "{\n"
        '  "sprint_title": "string",\n'
        '  "days": [\n'
        '    {"day": 1, "focus_skill": "string", "task": "string", "deliverable": "string"}\n'
        "  ],\n"
        '  "recommended_project": {\n'
        '    "title": "string",\n'
        '    "stack": ["string"],\n'
        '    "why_it_helps": "string"\n'
        "  }\n"
        "}\n"
        "Include all 14 days (day 1 through day 14) with specific, actionable tasks and concrete daily deliverables."
    )

    user_prompt = (
        f"Target Role: {target_role}\n"
        f"Intensity Mode: {intensity_mode}\n"
        f"Missing Skills to Master: {skills_str}\n"
        "Create the 14-day sprint roadmap in JSON format."
    )

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    raw_content = completion.choices[0].message.content
    return json.loads(raw_content)


if __name__ == "__main__":
    print("Testing Vaibhav's Roadmap AI Agent...\n")
    result = generate_sprint_roadmap(
        target_role="Software Engineer",
        missing_skills=["Docker", "System Design", "AWS Deployment"],
        intensity_mode="Hell Mode"
    )
    print(json.dumps(result, indent=2))
