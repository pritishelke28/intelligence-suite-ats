# 🟢 Intelligence Suite: AI-Powered Talent Acquisition

An advanced Applicant Tracking System (ATS) built with **Flask** and **Natural Language Processing**. This platform automates the recruitment workflow by scoring resumes against job descriptions using TF-IDF vectorization and Cosine Similarity.

## ✨ Key Features
- **AI-Powered Screening:** Automated ATS scoring to identify top talent instantly using Cosine Similarity.
- **Semantic Skill Analysis:** Automatic extraction of matching, missing, and auxiliary skills from candidate resumes.
- **Emerald Dark UI:** A premium, high-performance interface designed for modern recruitment.
- **Candidate Insights:** Deep-dive reports for applicants showing exactly how they match the job criteria.
- **Recruiter Mission Control:** Centralized dashboard to manage job postings, applicants, and statuses.

## 🛠️ Tech Stack
- **Backend:** Python / Flask
- **AI/ML:** Scikit-learn (TF-IDF), NLTK (Lemmatization & Preprocessing)
- **Database:** SQLite3
- **Parsing:** PyPDF2 / pypdf
- **Frontend:** Bootstrap 5 with Glassmorphism CSS

## 🔧 Installation & Launch
1. **Clone the repository:**
   `git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git`
2. **Install dependencies:**
   `pip install -r requirements.txt`
3. **Initialize NLP models (Run in Python):**
   ```python
   import nltk
   nltk.download(['stopwords', 'wordnet'])

