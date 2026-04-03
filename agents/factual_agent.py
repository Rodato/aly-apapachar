#!/usr/bin/env python3
"""
Factual Agent - Aly Apapachar
Recupera contexto del conocimiento de Equimundo y genera una respuesta factual y conservadora.
intent: FACTUAL
"""

from typing import Dict, List

from rag.multi_collection_rag import MultiCollectionRAG

from .base_agent import BaseAgent, AgentState


class FactualAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="factual_agent",
            description="Recupera contexto y responde consultas factuales sobre programas de Equimundo"
        )
        try:
            self.rag_system = MultiCollectionRAG(["apapachar", "aly_general_knowledge"])
            self.logger.info("✅ Factual Agent inicializado (multi-colección)")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando Factual Agent: {e}")
            self.rag_system = None

    def process(self, state: AgentState) -> AgentState:
        self.log_processing(state, f"Buscando: '{state.user_input[:50]}...'")

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
                result = self.rag_system.generate_answer(
                    state.user_input, chunks, state.language_config
                )
                state.response = result['answer']
                state.sources = self._format_sources(chunks)
                self.log_processing(state, f"Respuesta generada con {len(chunks)} chunks de {collections}")

        except Exception as e:
            self.logger.error(f"❌ Error en Factual Agent: {e}")
            state.response = self._error_msg(state.language_config)
            state.sources = []

        return state

    def _no_context_msg(self, language_config: Dict) -> str:
        if not language_config:
            return "No encontré información relevante para tu pregunta."
        code = language_config.get('code', 'es')
        if code == 'en':
            return "I couldn't find relevant information for your question. Could you rephrase it?"
        elif code == 'pt':
            return "Não encontrei informações relevantes para sua pergunta. Você poderia reformular?"
        return "No encontré información relevante para tu pregunta. ¿Podrías reformularla?"

    def _error_msg(self, language_config: Dict) -> str:
        if not language_config:
            return "Error procesando tu consulta. Intenta de nuevo."
        code = language_config.get('code', 'es')
        if code == 'en':
            return "Error processing your query. Please try again."
        elif code == 'pt':
            return "Erro ao processar sua consulta. Tente novamente."
        return "Error procesando tu consulta. Intenta de nuevo."

    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        return [
            {
                "document": item['chunk'].get('document_name', ''),
                "section": item['chunk'].get('section_header', item['chunk'].get('theme_category', '')),
                "collection": item.get('collection', ''),
                "similarity": round(item['similarity'], 3),
                "preview": item['chunk']['content'][:200] + "..."
            }
            for item in chunks[:3]
        ]
