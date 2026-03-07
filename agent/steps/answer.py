import os
from exa_py import Exa

exa = Exa(api_key=os.environ["EXA_API_KEY"])

def answer_questions(name: str) -> dict:
    questions = {
        "projects":    f"What are the most notable technical projects or products built by {name}?",
        "expertise":   f"What are the core technical skills and areas of expertise of {name}?",
        "impact":      f"What measurable impact or achievements has {name} had in their career?",
        "personality": f"How does {name} communicate online? What is their tone — technical, casual, creative, academic, humorous?",
        "aesthetics":  f"Does {name} show any visual design taste, aesthetic preferences, or creative sensibility in their work or online presence?"
    }
    answers = {}
    for key, question in questions.items():
        try:
            resp = exa.answer(question, text=True)
            answers[key] = resp.answer
        except Exception as e:
            answers[key] = f"[unavailable: {e}]"
    return answers
