#!/usr/bin/env python3
"""
Ideate Agent - Aly Apapachar
Genera IDEAS CREATIVAS e INSPIRADORAS basadas en el Manual A+P.
Modelo: mistralai/mistral-small-creative | Temperatura: 0.8
"""

import os
import requests
from typing import Dict, List

from rag.simple_rag_mongo import SimpleMongoRAG

from .base_agent import BaseAgent, AgentState

DOCUMENT_FILTER = {"document_name": {"$regex": "MANUAL A\\+P_vICBF", "$options": "i"}}

MODEL = "mistralai/mistral-small-creative"
TEMPERATURE = 0.8


class IdeateAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="ideate_agent",
            description="Genera ideas creativas basadas en el Manual A+P"
        )
        try:
            self.rag_system = SimpleMongoRAG()
            self.logger.info(f"✅ Ideate Agent inicializado ({MODEL})")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando Ideate Agent: {e}")
            self.rag_system = None

        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }

    def process(self, state: AgentState) -> AgentState:
        self.log_processing(state, f"Generando ideas: '{state.user_input[:50]}...'")

        if not self.rag_system:
            state.response = self._error_msg(state.language_config)
            state.sources = []
            return state

        try:
            if state.language_config:
                self.rag_system.session_language = state.language
                self.rag_system.language_config = state.language_config

            chunks = self.rag_system.search_chunks(state.user_input, top_k=4, filters=DOCUMENT_FILTER)

            if not chunks:
                state.response = self._no_context_msg(state.language_config)
                state.sources = []
            else:
                state.response = self._generate(state.user_input, chunks, state.language_config)
                state.sources = self._format_sources(chunks)
                self.log_processing(state, f"Ideas generadas con {len(chunks)} chunks")

        except Exception as e:
            self.logger.error(f"❌ Error en Ideate Agent: {e}")
            state.response = self._error_msg(state.language_config)
            state.sources = []

        return state

    def _generate(self, query: str, chunks: List[Dict], language_config: Dict) -> str:
        lang = language_config.get('code', 'es') if language_config else 'es'

        context = "\n\n".join([
            f"[{c['chunk']['section_header']}]\n{c['chunk']['content']}"
            for c in chunks[:4]
        ])

        if lang == 'en':
            prompt = f"""You are a creative facilitator of the Apapáchar (A+P) program.
Your role is to INSPIRE and generate NEW CREATIVE IDEAS for facilitators, grounded in the program's spirit.
Use the manual as a foundation but think beyond it — suggest variations, dynamic activities, fresh angles.
Be imaginative, warm, and encouraging.

Manual context (for inspiration):
{context}

Request: {query}

Creative ideas:"""

        elif lang == 'pt':
            prompt = f"""Você é um facilitador criativo do programa Apapáchar (A+P).
Seu papel é INSPIRAR e gerar NOVAS IDEIAS CRIATIVAS para facilitadores, com base no espírito do programa.
Use o manual como base, mas pense além dele — sugira variações, atividades dinâmicas, ângulos frescos.
Seja imaginativo, caloroso e encorajador.

Contexto do manual (para inspiração):
{context}

Solicitação: {query}

Ideias criativas:"""

        else:
            prompt = f"""Eres un facilitador creativo del programa Apapáchar (A+P).
Tu rol es INSPIRAR y generar NUEVAS IDEAS CREATIVAS para facilitadores, ancladas en el espíritu del programa.
Usa el manual como base pero piensa más allá — sugiere variaciones, actividades dinámicas, ángulos frescos.
Sé imaginativo, cálido y motivador.

Contexto del manual (para inspiración):
{context}

Solicitud: {query}

Ideas creativas:"""

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": TEMPERATURE
                },
                timeout=45
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            self.logger.error(f"❌ Error generando ideas: {e}")
            return self._error_msg(language_config)

    def _no_context_msg(self, language_config: Dict) -> str:
        code = language_config.get('code', 'es') if language_config else 'es'
        if code == 'en':
            return "I couldn't find relevant content in the A+P Manual for this. Could you give me more context?"
        if code == 'pt':
            return "Não encontrei conteúdo relevante no Manual A+P para isso. Você poderia me dar mais contexto?"
        return "No encontré contenido relevante en el Manual A+P para esto. ¿Podrías darme más contexto?"

    def _error_msg(self, language_config: Dict) -> str:
        code = language_config.get('code', 'es') if language_config else 'es'
        if code == 'en':
            return "Error generating ideas. Please try again."
        if code == 'pt':
            return "Erro ao gerar ideias. Tente novamente."
        return "Error generando ideas. Intenta de nuevo."

    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        return [
            {
                "document": c['chunk']['document_name'],
                "section": c['chunk']['section_header'],
                "similarity": round(c['similarity'], 3),
                "preview": c['chunk']['content'][:200] + "..."
            }
            for c in chunks[:3]
        ]
