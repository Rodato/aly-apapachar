#!/usr/bin/env python3
"""
RAG Agent - Aly Apapachar
Responde SOLO con información del Manual A+P (ICBF).
El filtro de documento está hardcodeado.
"""

import os
from typing import Dict, List

from rag.simple_rag_mongo import SimpleMongoRAG

from .base_agent import BaseAgent, AgentState

# Filtro fijo: solo el Manual A+P vICBF
DOCUMENT_FILTER = {"document_name": {"$regex": "MANUAL A\\+P_vICBF", "$options": "i"}}


class ApapacharRAGAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="apapachar_rag_agent",
            description="Responde consultas usando el Manual A+P (ICBF)"
        )
        try:
            self.rag_system = SimpleMongoRAG()
            self.logger.info("✅ RAG system inicializado (filtrado a Manual A+P vICBF)")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando RAG: {e}")
            self.rag_system = None

    def process(self, state: AgentState) -> AgentState:
        self.log_processing(state, f"Buscando en Manual A+P: '{state.user_input[:50]}...'")

        if not self.rag_system:
            state.response = self._error_msg(state.language_config)
            state.sources = []
            return state

        try:
            # Configurar idioma
            if state.language_config:
                self.rag_system.session_language = state.language
                self.rag_system.language_config = state.language_config

            # Buscar SIEMPRE con el filtro del documento
            chunks = self.rag_system.search_chunks(
                state.user_input,
                top_k=4,
                filters=DOCUMENT_FILTER
            )

            if not chunks:
                state.response = self._no_context_msg(state.language_config)
                state.sources = []
            else:
                result = self.rag_system.generate_answer(state.user_input, chunks)
                state.response = result['answer']
                state.sources = self._format_sources(chunks)
                self.log_processing(state, f"Respuesta generada con {len(chunks)} chunks")

        except Exception as e:
            self.logger.error(f"❌ Error en RAG: {e}")
            state.response = self._error_msg(state.language_config)
            state.sources = []

        return state

    def _no_context_msg(self, language_config: Dict) -> str:
        if not language_config:
            return "No encontré información relevante en el Manual A+P para tu pregunta."
        code = language_config.get('code', 'es')
        if code == 'en':
            return "I couldn't find relevant information in the A+P Manual for your question. Could you rephrase it?"
        elif code == 'pt':
            return "Não encontrei informações relevantes no Manual A+P para sua pergunta. Você poderia reformular?"
        return "No encontré información relevante en el Manual A+P para tu pregunta. ¿Podrías reformularla?"

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
                "document": item['chunk']['document_name'],
                "section": item['chunk']['section_header'],
                "similarity": round(item['similarity'], 3),
                "preview": item['chunk']['content'][:200] + "..."
            }
            for item in chunks[:3]
        ]
