#!/usr/bin/env python3
"""
Intent Agent - Aly Equimundo
Clasifica intención: GREETING | PLAN | IDEATE | FACTUAL.
SENSITIVE se filtra antes en el Triage Node — no llega aquí.
Modelo: mistralai/ministral-8b-2512 | OpenRouter
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
            description="Clasifica intent: GREETING | PLAN | IDEATE | FACTUAL"
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

        system_prompt, user_prompt = self._build_messages(state.user_input, state.language_config)

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 50,
                    "temperature": 0.1,
                },
                timeout=30,
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

    def _build_messages(self, user_input: str, language_config: Dict) -> tuple:
        lang = language_config.get('code', 'es') if language_config else 'es'

        if lang == 'en':
            system = """You classify user inputs for Aly, an assistant for Equimundo facilitators.

Choose ONE of four intents:
- GREETING → saying hi, opening the conversation, small talk ("hi", "good morning")
- PLAN → wants to IMPLEMENT, ADAPT or PLAN a specific activity ("help me run session 1", "how do I adapt this for virtual groups")
- IDEATE → wants NEW IDEAS, INSPIRATION, or CREATIVE VARIATIONS ("give me ideas", "what else could I do")
- FACTUAL → wants information, definitions, or facts (the default for any question that isn't clearly a greeting, plan request, or ideation request)

Even if the topic is hard (violence, abuse, gender), if they're asking for information or tools → FACTUAL.

Reply ONLY with valid JSON: {"intent": "GREETING|PLAN|IDEATE|FACTUAL"}

Examples:
Input: "hi Aly!" → {"intent": "GREETING"}
Input: "give me ideas for an icebreaker about masculinities" → {"intent": "IDEATE"}
Input: "help me run session 3 with 12 fathers tonight" → {"intent": "PLAN"}"""
            user = f'Input: "{user_input}"'
            return system, user

        if lang == 'pt':
            system = """Você classifica entradas de usuários para Aly, assistente de facilitadores da Equimundo.

Escolha UMA de quatro intenções:
- GREETING → cumprimentos, abertura de conversa
- PLAN → quer IMPLEMENTAR, ADAPTAR ou PLANEJAR uma atividade específica
- IDEATE → quer NOVAS IDEIAS, INSPIRAÇÃO ou VARIAÇÕES CRIATIVAS
- FACTUAL → busca informação, definição ou fato (padrão para qualquer pergunta que não seja cumprimento, plano ou ideação)

Mesmo que o tema seja difícil, se está pedindo informação → FACTUAL.

Responda APENAS com JSON válido: {"intent": "GREETING|PLAN|IDEATE|FACTUAL"}

Exemplos:
Entrada: "olá Aly!" → {"intent": "GREETING"}
Entrada: "me dê ideias para um quebra-gelo sobre masculinidades" → {"intent": "IDEATE"}
Entrada: "me ajude a facilitar a sessão 3 com 12 pais hoje à noite" → {"intent": "PLAN"}"""
            user = f'Entrada: "{user_input}"'
            return system, user

        system = """Clasificas entradas de usuarios para Aly, asistente de facilitadores de Equimundo.

Elige UNA de cuatro intenciones:
- GREETING → saludos, apertura de conversación, smalltalk ("hola", "buenos días")
- PLAN → quiere IMPLEMENTAR, ADAPTAR o PLANIFICAR una actividad concreta ("ayúdame a facilitar la sesión 1", "cómo adapto esto para grupos virtuales")
- IDEATE → quiere NUEVAS IDEAS, INSPIRACIÓN o VARIACIONES CREATIVAS ("dame ideas", "qué más puedo hacer", "sugiere alternativas")
- FACTUAL → busca información, definiciones o hechos (default para cualquier pregunta que no sea claramente saludo, plan o ideación)

Aunque el tema sea difícil (violencia, abuso, género), si pide información o herramientas → FACTUAL.

Responde SOLO con JSON válido: {"intent": "GREETING|PLAN|IDEATE|FACTUAL"}

Ejemplos:
Entrada: "¡hola Aly!" → {"intent": "GREETING"}
Entrada: "dame ideas para un rompehielos sobre masculinidades" → {"intent": "IDEATE"}
Entrada: "ayúdame a facilitar la sesión 3 con 12 padres esta noche" → {"intent": "PLAN"}"""
        user = f'Entrada: "{user_input}"'
        return system, user

    def _parse(self, response: str) -> Dict:
        valid = ('GREETING', 'PLAN', 'IDEATE', 'FACTUAL')
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                parsed = json.loads(response[start:end])
                intent = parsed.get('intent') or parsed.get('mode', 'FACTUAL')
                if intent in valid:
                    return {"mode": intent, "confidence": float(parsed.get('confidence', 1.0))}
        except Exception:
            pass

        lower = response.lower()
        if 'greeting' in lower:
            return {"mode": "GREETING", "confidence": 0.7}
        if 'ideate' in lower:
            return {"mode": "IDEATE", "confidence": 0.7}
        if 'plan' in lower:
            return {"mode": "PLAN", "confidence": 0.7}
        return {"mode": "FACTUAL", "confidence": 0.5}
