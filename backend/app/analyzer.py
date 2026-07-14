import os
import json
import random
import re
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def clean_json_response(raw_response: str) -> dict:
    """Cleans up markdown code block ticks and repairs common JSON issues from LLMs."""
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    # Repair trailing commas in arrays/objects
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed. Raw response: {raw_response}")
        raise e

def get_mock_analysis(resume_text: str) -> dict:
    """Generates a dynamic mock analysis when no API key is available."""
    text_lower = resume_text.lower()
    
    # Simple heuristics to detect field
    is_web = "react" in text_lower or "angular" in text_lower or "javascript" in text_lower or "html" in text_lower
    is_python = "python" in text_lower or "django" in text_lower or "fastapi" in text_lower or "pandas" in text_lower
    is_java = "java" in text_lower or "spring" in text_lower
    
    if is_web:
        score = random.randint(72, 88)
        summary = "Dynamic front-end developer with experience in modern JavaScript frameworks. Demonstrates strong capabilities in building responsive interfaces, though could benefit from deeper cloud deployment exposure."
        missing_skills = ["TypeScript", "Docker", "AWS (S3/EC2)", "Unit Testing (Jest)"]
        improvements = [
            "Quantify achievements: change 'responsible for code reviews' to 'led code reviews for 5 developers, reducing bugs by 15%'.",
            "Add a dedicated 'Projects' section to showcase personal or freelance web applications.",
            "List specific web accessibility standards (WCAG) if experienced."
        ]
        grammar = ["Ensure consistent capitalization for technology names (e.g., JavaScript vs Javascript)."]
        ats_score = random.randint(70, 85)
        ats_feedback = "Good standard layout. Standard headers are parsed correctly. Multiple column format might cause slight parsing issues in older ATS systems."
        formatting_issues = ["Double column layout detected. Consider using a single-column layout for optimal ATS scanning."]
        roles = ["Frontend Engineer", "Web Developer", "Software Engineer (UI)", "Full Stack Developer"]
    elif is_python:
        score = random.randint(75, 92)
        summary = "Backend software engineer specializing in Python development. Proficient in database modeling and API creation, showing strong focus on performance optimization and clean code practices."
        missing_skills = ["Redis", "Kubernetes", "CI/CD Pipelines (GitHub Actions)", "PostgreSQL"]
        improvements = [
            "Use stronger action verbs in bullet points (e.g., 'Architected', 'Optimized', 'Automated').",
            "Specify database optimization metrics (e.g., 'improved query performance by 30%').",
            "Include links to GitHub repositories for key projects."
        ]
        grammar = ["None found."]
        ats_score = random.randint(78, 90)
        ats_feedback = "Strong keyword matches for backend development. Simple and clean layout is highly compatible with ATS standards."
        formatting_issues = []
        roles = ["Backend Developer", "Python Engineer", "Data Engineer", "Software Engineer"]
    else:
        score = random.randint(65, 80)
        summary = "Motivated professional presenting a diverse set of experiences. The resume indicates strong soft skills and adaptability, but needs more technical details and specific metrics."
        missing_skills = ["Git / Version Control", "Agile Methodologies", "SQL Databases", "Cloud Computing Basics"]
        improvements = [
            "Structure experience using the STAR method (Situation, Task, Action, Result).",
            "Define a clear technical skills section separated by categories (languages, frameworks, tools).",
            "Tailor the resume to highlight specific technical keywords rather than general tasks."
        ]
        grammar = ["Check sentence punctuation under the second experience description."]
        ats_score = random.randint(60, 75)
        ats_feedback = "The layout is clean but lacks density of industry-specific keywords, which may rank it lower in candidate matches."
        formatting_issues = ["Heavy use of decorative divider lines which can confuse text flow readers."]
        roles = ["Junior Developer", "Technical Support Engineer", "QA Tester", "Associate Software Engineer"]

    return {
        "score": score,
        "summary": summary,
        "missing_skills": missing_skills,
        "suggested_improvements": improvements,
        "grammar_issues": grammar,
        "ats_compatibility": {
            "ats_score": ats_score,
            "feedback": ats_feedback,
            "formatting_issues": formatting_issues
        },
        "suggested_roles": roles
    }

def analyze_resume_text(resume_text: str) -> dict:
    """Sends the resume text to the selected LLM and parses the result."""
    
    # Check if API Keys are missing or placeholders, and use Mock Mode if so
    has_gemini = GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here"
    has_openai = OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here"
    
    if not has_gemini and not has_openai:
        # FALLBACK: Return mock analysis
        print("API keys not set. Running in MOCK mode.")
        return get_mock_analysis(resume_text)

    prompt = f"""
You are an expert ATS (Applicant Tracking System) optimizer and career consultant.
Analyze the following resume text and provide a structured assessment in JSON format.

Resume Text:
---
{resume_text}
---

Your response MUST be a single valid JSON object with the following structure:
{{
  "score": <integer between 0 and 100 representing overall quality>,
  "summary": "<a concise 2-3 sentence professional summary of the candidate's profile>",
  "missing_skills": [<list of important skills/technologies that are missing or should be highlighted based on their industry>],
  "suggested_improvements": [<list of specific, actionable advice to improve bullet points, layout, or phrasing>],
  "grammar_issues": [<list of spelling or grammar mistakes found, or say "None found" if clean>],
  "ats_compatibility": {{
    "ats_score": <integer between 0 and 100 indicating ATS compatibility>,
    "feedback": "<brief paragraph on how well this resume will be processed by standard ATS software, mentioning formatting/structure>",
    "formatting_issues": [<list of potential ATS parsing hurdles like tables, images, multiple columns, custom fonts, or headers/footers>]
  }},
  "suggested_roles": [<list of 3-5 job titles/roles this candidate is well-suited for>]
}}

Ensure the JSON is well-formed, valid, and contains no trailing commas.
CRITICAL: Double quotes inside string values must be properly escaped as \\\" (e.g. \\\"Senior\\\" Developer). Do not include any literal newlines inside string values; use \\n instead.
Return ONLY the raw JSON object.
"""

    if AI_PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a professional ATS resume scanner that outputs strict JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        result_text = response.choices[0].message.content
        return clean_json_response(result_text)

    else:  # default to gemini
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Using Gemini 3.5 Flash as the standard coding/text model
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return clean_json_response(response.text)
