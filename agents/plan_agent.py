#!/usr/bin/env python3
"""
Plan Agent - Aly Apapachar
Ayuda a IMPLEMENTAR y ADAPTAR actividades del Manual A+P.
Modelo: google/gemini-2.5-flash-lite | Temperatura: 0.5
"""

import os
import requests
from typing import Dict, List

from rag.simple_rag_mongo import SimpleMongoRAG

from .base_agent import BaseAgent, AgentState

DOCUMENT_FILTER = {"document_name": {"$regex": "MANUAL A\\+P_vICBF", "$options": "i"}}

MODEL = "google/gemini-2.5-flash-lite"
TEMPERATURE = 0.5


class PlanAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="plan_agent",
            description="Ayuda a implementar y adaptar actividades del Manual A+P"
        )
        try:
            self.rag_system = SimpleMongoRAG()
            self.logger.info(f"✅ Plan Agent inicializado ({MODEL})")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando Plan Agent: {e}")
            self.rag_system = None

        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }

    def process(self, state: AgentState) -> AgentState:
        self.log_processing(state, f"Planificando implementación: '{state.user_input[:50]}...'")

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
                self.log_processing(state, f"Plan generado con {len(chunks)} chunks")

        except Exception as e:
            self.logger.error(f"❌ Error en Plan Agent: {e}")
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
            prompt = f"""You are an expert facilitator of the Apapáchar (A+P) program.
Your role is to help facilitators IMPLEMENT and ADAPT program activities to specific contexts.
Base your response exclusively on the manual content provided.
Be practical, structured, and step-by-step. Adapt to the specific context mentioned.

Manual context:
{context}

Request: {query}

Practical implementation plan:"""

        elif lang == 'pt':
            prompt = f"""Você é um facilitador especialista do programa Apapáchar (A+P).
Seu papel é ajudar facilitadores a IMPLEMENTAR e ADAPTAR atividades do programa a contextos específicos.
Baseie sua resposta exclusivamente no conteúdo do manual fornecido.
Seja prático, estruturado e passo a passo. Adapte ao contexto específico mencionado.

Contexto do manual:
{context}

Solicitação: {query}

Plano prático de implementação:"""

        else:
            prompt = f"""Eres un facilitador experto del programa Apapáchar (A+P).
Tu rol es ayudar a facilitadores a IMPLEMENTAR y ADAPTAR actividades del programa a contextos específicos.
Basa tu respuesta exclusivamente en el contenido del manual proporcionado.
Sé práctico, estructurado y paso a paso. Adapta al contexto específico mencionado.

Contexto del manual:
{context}

Solicitud: {query}

Plan práctico de implementación:"""

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
            self.logger.error(f"❌ Error generando plan: {e}")
            return self._error_msg(language_config)

    def _no_context_msg(self, language_config: Dict) -> str:
        code = language_config.get('code', 'es') if language_config else 'es'
        if code == 'en':
            return "I couldn't find relevant content in the A+P Manual to help with this implementation. Could you be more specific?"
        if code == 'pt':
            return "Não encontrei conteúdo relevante no Manual A+P para ajudar nessa implementação. Você poderia ser mais específico?"
        return "No encontré contenido relevante en el Manual A+P para ayudarte con esta implementación. ¿Podrías ser más específico?"

    def _error_msg(self, language_config: Dict) -> str:
        code = language_config.get('code', 'es') if language_config else 'es'
        if code == 'en':
            return "Error generating the plan. Please try again."
        if code == 'pt':
            return "Erro ao gerar o plano. Tente novamente."
        return "Error generando el plan. Intenta de nuevo."

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
