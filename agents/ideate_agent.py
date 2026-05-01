#!/usr/bin/env python3
"""
Ideate Agent - Aly Equimundo
Genera ideas creativas e inspiradoras basadas en el conocimiento de Equimundo.
intent: IDEATE
Modelo: google/gemini-2.5-flash | Temperatura: 0.8
(swap desde mistralai/mistral-small-creative — bottleneck de latencia, ver project_ideate_latency)
"""

import os
import requests
from typing import Dict, List

from rag.multi_collection_rag import MultiCollectionRAG

from .base_agent import BaseAgent, AgentState

MODEL = "google/gemini-2.5-flash"
TEMPERATURE = 0.8
MAX_TOKENS = 700  # cap para WhatsApp (~ 1800 chars)


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

        system_prompt = """Eres Aly, asistente experta en programas de Equimundo. Ofreces 3 a 5 ideas de actividades inclusivas y seguras basadas en el tema o el objetivo del facilitador. Tu trabajo es ABRIR posibilidades — no dar una única respuesta final.

## ESTRUCTURA DE RESPUESTA (obligatoria):
*Tema:* <resumen en una línea>
Aquí hay algunas ideas para explorar:

*1- Título:* resumen en una línea
-> *Prueba:* ejemplo corto de frase o acción

*2- Título:* resumen en una línea
-> *Prueba:* ejemplo corto de frase o acción

*3- Título:* resumen en una línea
-> *Prueba:* ejemplo corto de frase o acción

Cierra con: "¿Quieres ayuda para adaptar alguna de estas a tu grupo?"

## REGLAS DE FORMATO (WhatsApp):
- Negrita con un solo *asterisco* (no doble, no markdown).
- Cada idea con "*N- Título:*" y subitem con "-> *Prueba:*".
- NUNCA uses encabezados con # ni barra invertida (\\) al final de línea.
- Máximo ~1800 caracteres. Cada idea debe caber en 2-3 líneas.

## TONO:
- Curioso, de apoyo y flexible.
- Nunca juzgues ni moralices.
- Evita términos académicos como "intervención" u "objetivo de aprendizaje".
- Valida la agencia del facilitador: "Tú conoces a tu grupo — adáptalo como necesites."

## TEMAS SENSIBLES:
Cuando el tema va más allá de la facilitación de sesiones (trauma, disciplina en casa, asuntos clínicos):
- Reconoce: "Ese es un tema muy importante. Aunque no puedo orientarte directamente sobre eso, aquí hay una forma de apoyar a los participantes de manera segura en tus sesiones."
- Luego ofrece la actividad de reflexión.

## INPUT POCO CLARO:
Si el input es vago, antes de las ideas pregunta: "Solo para asegurarme — ¿buscas: 1) Explorar nuevas ideas? o 2) Adaptar algo que ya usas?"

## EJEMPLO

Solicitud: "dame ideas para un rompehielos sobre masculinidades"
Contexto: [extractos del manual sobre dinámicas y masculinidades]
Respuesta:
*Tema:* Rompehielos para abrir una sesión sobre masculinidades.
Aquí hay algunas ideas para explorar:

*1- Mapa de palabras:* Cada participante escribe en un papel la primera palabra que asocia con "ser hombre".
-> *Prueba:* "Sin pensarlo mucho — la primera palabra que se te venga."

*2- Línea de acuerdo:* Lees afirmaciones ("los hombres no lloran") y el grupo se ubica en una línea de acuerdo/desacuerdo.
-> *Prueba:* "No hay respuesta correcta — vamos a mirar dónde se para cada quien."

*3- Objeto que me representa:* Cada uno trae o nombra un objeto que les conecta con la masculinidad que aprendieron.
-> *Prueba:* "Cuéntame qué objeto traes y por qué lo elegiste."

¿Quieres ayuda para adaptar alguna de estas a tu grupo?"""

        user_prompt = f"""## Contexto del manual (para inspiración):
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
