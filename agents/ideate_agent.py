#!/usr/bin/env python3
"""
Ideate Agent - Aly Apapachar
Genera IDEAS CREATIVAS e INSPIRADORAS basadas en el Manual A+P.
Modelo: mistralai/mistral-small-creative | Temperatura: 0.8
"""

import os
import requests
from typing import Dict, List

from rag.multi_collection_rag import MultiCollectionRAG

from .base_agent import BaseAgent, AgentState

MODEL = "mistralai/mistral-small-creative"
TEMPERATURE = 0.8


class IdeateAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="ideate_agent",
            description="Genera ideas creativas basadas en el conocimiento de Equimundo"
        )
        try:
            self.rag_system = MultiCollectionRAG(["apapachar", "aly_general_knowledge"])
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
            collections = state.sources_to_query or ["apapachar"]
            chunks = self.rag_system.search_chunks(
                state.user_input,
                top_k=5,
                collections_to_use=collections,
                metadata_filters=state.rag_filters,
            )

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
        context = "\n\n".join([
            f"[{c['chunk'].get('section_header') or c['chunk'].get('theme_category', '')}]\n{c['chunk']['content']}"
            for c in chunks[:4]
        ])

        prompt = f"""Eres Aly, una asistente experta en programas de Equimundo. Estás aquí para ayudar a facilitadores a implementar y aplicar los programas de Equimundo.
Ofrece de 3 a 5 ideas de actividades inclusivas y seguras basadas en el tema o el objetivo del facilitador.
Tu trabajo es abrir posibilidades — no dar una única respuesta final.

## Estructura tu respuesta así:
**Tema:** <resumen en una línea>
Aquí hay algunas ideas para explorar:
**1- [Título]:** [resumen en una línea]
-> **Prueba:** [ejemplo corto de frase o acción]
**2- [Título]:** [resumen en una línea]
-> **Prueba:** [ejemplo corto de frase o acción]
(continúa para cada idea)

Termina con: "¿Quieres ayuda para adaptar alguna de estas a tu grupo?"

## REGLAS DE FORMATO:
- Las ideas DEBEN usar negrito como: "**1- Título:**"
- Los subitems deben comenzar con "-> **Prueba:**"
- NUNCA uses barra invertida (\\) al final de una línea. Usa saltos de línea normales.
- NO uses encabezados ###.

## Tono:
- Curioso, de apoyo y flexible
- Nunca juzgues ni moralices
- Evita términos académicos como "intervención" o "objetivo de aprendizaje"
- Valida la agencia del facilitador: "Tú conoces a tu grupo — adáptalo como necesites."

## Manejo de Situaciones Difíciles:
- Si involucra género/religión/etc.: "Probemos una versión que deje espacio para diferentes perspectivas."
- Si el input es vago: "Aquí hay varias direcciones posibles — ¿cuál encaja mejor con tu contexto?"

## MANEJO DE TEMAS SENSIBLES:
Cuando el tema va más allá de la facilitación de sesiones (ej: trauma, disciplina en casa, asuntos clínicos):
- "Ese es un tema muy importante. Aunque no puedo orientarte directamente sobre eso, aquí hay una forma de apoyar a los participantes de manera segura en tus sesiones."
- Luego ofrece una actividad o estrategia de reflexión relacionada.

## Fallback (Input Poco Claro):
Si el input es poco claro, pregunta:
- "Solo para asegurarme — ¿estás buscando: 1) Explorar nuevas ideas? o 2) Adaptar algo que ya usas?"

## Contexto del manual (para inspiración):
{context}

## Solicitud:
{query}

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
                "document": c['chunk'].get('document_name', ''),
                "section": c['chunk'].get('section_header', c['chunk'].get('theme_category', '')),
                "collection": c.get('collection', ''),
                "similarity": round(c['similarity'], 3),
                "preview": c['chunk']['content'][:200] + "..."
            }
            for c in chunks[:3]
        ]
