import os
import json
import requests
import re
from groq import Groq
from django.conf import settings


class IAClient:
    """
    Client IA mixte :
    - Groq  → génération questions + feedback global (rapide)
    - Ollama → évaluation réponses (privé, local)
    """

    def __init__(self):
        self.groq = Groq(api_key=settings.GROQ_API_KEY)
        self.groq_model = settings.GROQ_MODEL

    # ==========================================
    # GROQ — Génération rapide
    # ==========================================

    def generer_questions(self, contexte, poste_vise):
        """
        Génère 5 questions d'entretien via Groq
        """
        prompt = f"""
        Tu es un recruteur expert. Génère exactement 5 questions d'entretien
        pour le profil suivant :

        {contexte}

        Génère un mélange :
        - 2 questions TECHNIQUE
        - 1 questions COMPORTEMENTALE
        - 1 questions SITUATIONNELLE
        - 1 questions MOTIVATION

        Réponds UNIQUEMENT avec un JSON valide :
        {{
            "questions": [
                {{"ordre": 1, "type": "TECHNIQUE", "question": "..."}},
                {{"ordre": 2, "type": "COMPORTEMENTALE", "question": "..."}},
                {{"ordre": 3, "type": "SITUATIONNELLE", "question": "..."}},
                {{"ordre": 4, "type": "MOTIVATION", "question": "..."}},
                {{"ordre": 5, "type": "TECHNIQUE", "question": "..."}},
            ]
        }}
        """

        response = self.groq.chat.completions.create(
            model=self.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )

        texte = response.choices[0].message.content.strip()
        print("🚀 GROQ → génération questions")

        # Nettoyer JSON
        if '```json' in texte:
            texte = texte.split('```json')[1].split('```')[0]
        elif '```' in texte:
            texte = texte.split('```')[1].split('```')[0]

        data = json.loads(texte.strip())
        return data['questions']

    def generer_feedback_global(self, session):
        """
        Génère le feedback global de la session via Groq
        """
        questions = session.questions.all()

        resume = "\n".join([
            f"Q{q.ordre} ({q.get_type_question_display()}): {q.question}\n"
            f"Réponse: {q.reponse_candidat[:150]}\n"
            f"Score: {q.score}/10"
            for q in questions if q.reponse_candidat
        ])

        prompt = f"""
        Tu es un recruteur expert. Donne un feedback global bienveillant
        sur cette session d'entretien.

        Poste visé: {session.poste_vise}
        Score moyen: {session.score_global}/10

        Résumé:
        {resume[:2000]}

        Donne un feedback en français avec :
        - 2 points forts globaux
        - 2 axes d'amélioration
        - 1 conseil final encourageant

        Sois bienveillant et constructif.
        """

        response = self.groq.chat.completions.create(
            model=self.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        print("🧠 GROQ → feedback global")

        return response.choices[0].message.content.strip()
    
    def _evaluer_reponse_groq(self, question, reponse, poste_vise):
        """
        Fallback — évalue via Groq si Ollama échoue
        """
        prompt = f"""
        Évalue cette réponse d'entretien pour le poste: {poste_vise}
        Question: {question.question}
        Réponse: {reponse}

        Réponds UNIQUEMENT avec un JSON :
        {{
            "score": 7.0,
            "feedback": "...",
            "points_forts": ["..."],
            "points_amelioration": ["..."]
        }}
        """

        response = self.groq.chat.completions.create(
            model=self.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300,
        )

        print("🔁 GROQ → fallback évaluation")

        texte = response.choices[0].message.content.strip()
        if '```json' in texte:
            texte = texte.split('```json')[1].split('```')[0]
        elif '```' in texte:
            texte = texte.split('```')[1].split('```')[0]

        data = self.clean_json(texte)

        return {
            'score': float(data.get('score', 5.0)),
            'feedback': data.get('feedback', ''),
            'points_forts': data.get('points_forts', []),
            'points_amelioration': data.get('points_amelioration', [])
        }

    def clean_json(self, texte):

        # Cherche le JSON entre { ... }
        match = re.search(r'\{.*\}', texte, re.DOTALL)
        if match:
            return json.loads(match.group())

        # Si rien trouvé → erreur
        raise ValueError("JSON introuvable")