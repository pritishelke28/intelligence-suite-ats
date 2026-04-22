import re

def extract_skills(resume_text, required):
    resume_text = resume_text.lower()
    found, missing = [], []

    for s in required:
        if s in resume_text:
            found.append(s)
        else:
            missing.append(s)

    return found, missing

def extract_experience(text):
    years = re.findall(r"(\d+)\+?\s+years?", text.lower())
    return max(map(int, years)) if years else 0
