import re
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download("stopwords")
nltk.download("wordnet")

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))

# ---------------- PDF TEXT ----------------
def extract_text_from_pdf(pdf_path):
    text = ""
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

# ---------------- CLEAN TEXT ----------------
def preprocess_text(text):
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    text = text.lower()
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words]
    return " ".join(tokens)

# ---------------- SCORE RESUME ----------------
def calculate_score(resume_text, job_description):
    documents = [
        preprocess_text(job_description),
        preprocess_text(resume_text)
    ]

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(documents)

    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(score * 100, 2)