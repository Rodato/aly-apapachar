#!/usr/bin/env python3
"""
Plan Agent - Aly Apapachar
Ayuda a IMPLEMENTAR y ADAPTAR actividades del Manual A+P.
Modelo: google/gemini-2.5-flash-lite | Temperatura: 0.5
"""

import os
import requests
from typing import Dict, List

from rag.multi_collection_rag import MultiCollectionRAG

from .base_agent import BaseAgent, AgentState

MODEL = "google/gemini-2.5-flash-lite"
TEMPERATURE = 0.5


class PlanAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="plan_agent",
            description="Ayuda a implementar y adaptar actividades de Equimundo"
        )
        try:
            self.rag_system = MultiCollectionRAG(["apapachar", "aly_general_knowledge"])
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
                self.log_processing(state, f"Plan generado con {len(chunks)} chunks")

        except Exception as e:
            self.logger.error(f"❌ Error en Plan Agent: {e}")
            state.response = self._error_msg(state.language_config)
            state.sources = []

        return state

    def _generate(self, query: str, chunks: List[Dict], language_config: Dict) -> str:
        context = "\n\n".join([
            f"[{c['chunk'].get('section_header') or c['chunk'].get('theme_category', '')}]\n{c['chunk']['content']}"
            for c in chunks[:4]
        ])

        prompt = f"""Eres Aly, una asistente experta en programas de Equimundo. Estás aquí para ayudar a facilitadores a implementar y aplicar los programas de Equimundo.
Ayuda al facilitador a convertir una actividad conocida, un desafío o un objetivo en un plan pequeño, claro y realista que pueda aplicar en su próxima sesión.

## Estructura tu respuesta así:
**Tema:** <resumen en una línea de lo que el facilitador quiere hacer>
**Plan Sugerido:**
1- **[Nombre del Paso]:** ...
2- **[Nombre del Paso]:** ...
3- **[Nombre del Paso]:** ...

**Consejos:**
-> ...
-> ...

**Frase de Ejemplo:** "..."

Recordatorio: Puedes ajustar esto según las necesidades de tu grupo.

## REGLAS DE FORMATO:
- Los pasos numerados DEBEN usar negrito como: "1- **Título:**"
- Los subitems deben comenzar con "-> "
- NUNCA uses barra invertida (\\) al final de una línea. Usa saltos de línea normales.
- NO uses encabezados ###.

## Capa de Seguridad:
- Si el facilitador parece sobrecargado, comienza con: "Desglosemos esto en una sola cosa pequeña que puedas intentar."
- Si el tema toca género/identidad: "Esto puede ser sensible — aquí hay una forma de invitar a la reflexión sin forzar la exposición."

## Restricciones:
- Nunca inventes estrategias. Solo adapta lo que ya está presente en el contexto del manual.
- No des consejos sobre terapia familiar, tratamiento clínico o cuestiones de identidad.

## Contexto del manual:
{context}

## Solicitud:
{query}

Respuesta:"""

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
                "document": c['chunk'].get('document_name', ''),
                "section": c['chunk'].get('section_header', c['chunk'].get('theme_category', '')),
                "collection": c.get('collection', ''),
                "similarity": round(c['similarity'], 3),
                "preview": c['chunk']['content'][:200] + "..."
            }
            for c in chunks[:3]
        ]
