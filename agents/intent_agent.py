#!/usr/bin/env python3
"""
Intent Agent - Aly Apapachar
Detecta si el mensaje es GREETING, SENSITIVE, o FACTUAL (default).
Versión simplificada - solo un documento.
"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict

from .base_agent import BaseAgent, AgentState

load_dotenv()


class IntentAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="intent_agent",
            description="Detecta intención: GREETING | SENSITIVE | FACTUAL"
        )
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")

        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "mistralai/ministral-8b-2512"
        self.logger.info("✅ Intent Agent inicializado")

    def process(self, state: AgentState) -> AgentState:
        self.log_processing(state, f"Detectando intent: '{state.user_input[:50]}...'")

        prompt = self._build_prompt(state.user_input, state.language_config)

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.1
                },
                timeout=30
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            result = self._parse(content)
        except Exception as e:
            self.logger.error(f"❌ Error detectando intent: {e}")
            result = {"mode": "FACTUAL", "confidence": 0.5}

        state.mode = result["mode"]
        state.mode_confidence = result["confidence"]
        self.log_processing(state, f"Intent: {state.mode} ({state.mode_confidence})")
        return state

    def _build_prompt(self, user_input: str, language_config: Dict) -> str:
        lang = language_config.get('code', 'es') if language_config else 'es'

        if lang == 'en':
            return f"""Classify this user input into one of five intents for the Apapáchar parenting program:

User input: "{user_input}"

Intents:
- GREETING → User is saying hello or starting the conversation
- PLAN → User wants to IMPLEMENT, ADAPT or PLAN specific activities (e.g. "help me run session 1", "how do I adapt this for virtual groups")
- IDEATE → User wants NEW IDEAS, INSPIRATION or CREATIVE VARIATIONS (e.g. "give me ideas", "what else could I do", "suggest alternatives")
- SENSITIVE → Topic involves trauma, abuse, family conflict, mental health crisis
- FACTUAL → User seeks specific information, definitions or facts from the manual

Respond ONLY with valid JSON:
{{"intent": "GREETING|PLAN|IDEATE|SENSITIVE|FACTUAL", "confidence": 0.0-1.0}}"""

        elif lang == 'pt':
            return f"""Classifique esta entrada do usuário em uma das cinco intenções para o programa de parentalidade Apapáchar:

Entrada: "{user_input}"

Intenções:
- GREETING → Usuário está dizendo olá ou iniciando a conversa
- PLAN → Usuário quer IMPLEMENTAR, ADAPTAR ou PLANEJAR atividades específicas
- IDEATE → Usuário quer NOVAS IDEIAS, INSPIRAÇÃO ou VARIAÇÕES CRIATIVAS
- SENSITIVE → Tópico envolve trauma, abuso, conflito familiar, crise de saúde mental
- FACTUAL → Usuário busca informação específica, definições ou fatos do manual

Responda APENAS com JSON válido:
{{"intent": "GREETING|PLAN|IDEATE|SENSITIVE|FACTUAL", "confidence": 0.0-1.0}}"""

        else:
            return f"""Clasifica esta entrada del usuario en una de cinco intenciones para el programa de crianza Apapáchar:

Entrada: "{user_input}"

Intenciones:
- GREETING → El usuario está saludando o iniciando la conversación
- PLAN → El usuario quiere IMPLEMENTAR, ADAPTAR o PLANIFICAR actividades concretas (ej: "ayúdame a facilitar la sesión 1", "cómo adapto esto para grupos virtuales")
- IDEATE → El usuario quiere NUEVAS IDEAS, INSPIRACIÓN o VARIACIONES CREATIVAS (ej: "dame ideas", "qué más puedo hacer", "sugiere alternativas")
- SENSITIVE → El tema involucra trauma, abuso, conflicto familiar, crisis de salud mental
- FACTUAL → El usuario busca información específica, definiciones o hechos del manual

Responde SOLO con JSON válido:
{{"intent": "GREETING|PLAN|IDEATE|SENSITIVE|FACTUAL", "confidence": 0.0-1.0}}"""

    def _parse(self, response: str) -> Dict:
        valid = ('GREETING', 'PLAN', 'IDEATE', 'SENSITIVE', 'FACTUAL')
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                parsed = json.loads(response[start:end])
                intent = parsed.get('intent') or parsed.get('mode', 'FACTUAL')
                if intent in valid:
                    return {"mode": intent, "confidence": float(parsed.get('confidence', 0.7))}
        except Exception:
            pass

        lower = response.lower()
        if 'greeting' in lower:
            return {"mode": "GREETING", "confidence": 0.7}
        if 'ideate' in lower:
            return {"mode": "IDEATE", "confidence": 0.7}
        if 'plan' in lower:
            return {"mode": "PLAN", "confidence": 0.7}
        if 'sensitive' in lower:
            return {"mode": "SENSITIVE", "confidence": 0.7}
        return {"mode": "FACTUAL", "confidence": 0.5}
