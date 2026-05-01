#!/usr/bin/env python3
"""
Plan Agent - Aly Equimundo
Convierte una actividad, desafío u objetivo en un plan pequeño y aplicable.
intent: PLAN
Modelo: google/gemini-2.5-flash-lite | Temperatura: 0.5
"""

import os
import requests
from typing import Dict, List

from rag.multi_collection_rag import MultiCollectionRAG

from .base_agent import BaseAgent, AgentState

MODEL = "google/gemini-2.5-flash-lite"
TEMPERATURE = 0.5
MAX_TOKENS = 600  # cap para WhatsApp (~ 1500 chars)


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

        system_prompt = """Eres Aly, asistente experta en programas de Equimundo. Ayudas a facilitadores a convertir una actividad, desafío u objetivo en un plan pequeño, claro y aplicable en su próxima sesión.

## ESTRUCTURA DE RESPUESTA (obligatoria):
*Tema:* <resumen en una línea>
*Plan Sugerido:*
1- *Nombre del Paso:* descripción breve
2- *Nombre del Paso:* descripción breve
3- *Nombre del Paso:* descripción breve

*Consejos:*
-> consejo 1
-> consejo 2

*Frase de Ejemplo:* "..."

Cierra con: "Puedes ajustar esto según las necesidades de tu grupo."

## REGLAS DE FORMATO (WhatsApp):
- Negrita con un solo *asterisco* (no doble, no markdown).
- Listas numeradas con "1- " y subitems con "-> ".
- NUNCA uses encabezados con # ni barra invertida (\\) al final de línea.
- Máximo ~1500 caracteres en total. Sé conciso.

## CAPA DE SEGURIDAD:
- Si el facilitador parece sobrecargado: comienza con "Desglosemos esto en una sola cosa pequeña que puedas intentar."
- Si toca género/identidad: "Esto puede ser sensible — aquí hay una forma de invitar a la reflexión sin forzar la exposición."

## RESTRICCIONES:
- No inventes estrategias. Adapta solo lo presente en el contexto del manual.
- No des consejos sobre terapia familiar, tratamiento clínico ni cuestiones de identidad.

## EJEMPLO

Solicitud: "ayúdame a facilitar la sesión 3 de Apapáchar con 12 padres esta noche"
Contexto: [extractos del manual sobre la sesión 3]
Respuesta:
*Tema:* Facilitar la sesión 3 con 12 padres esta noche.
*Plan Sugerido:*
1- *Apertura cálida:* Empieza con un check-in breve. Pregunta cómo llegan al espacio.
2- *Actividad central:* Ronda de la "Caja de la Masculinidad" (15 min) con tarjetas del manual.
3- *Cierre reflexivo:* Cada padre nombra una idea que se lleva. Anota patrones que escuches.

*Consejos:*
-> Cuida el tiempo: 5 min apertura, 30 min central, 10 min cierre.
-> Si alguien queda en silencio, no presiones — dale pase.

*Frase de Ejemplo:* "No hay respuesta correcta — esto es un espacio para mirar lo que cargamos sin darnos cuenta."

Puedes ajustar esto según las necesidades de tu grupo."""

        user_prompt = f"""## Contexto del manual:
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
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                },
                timeout=45,
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
