#!/usr/bin/env python3
"""
Simple RAG with MongoDB - Aly Apapachar
Versión local extraída de puddleAsistant. Sin dependencia cruzada de proyectos.
"""

import os
import logging
from typing import List, Dict
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleMongoRAG:
    """RAG simple usando MongoDB para búsqueda semántica."""

    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME")
        self.collection_name = os.getenv("MONGODB_COLLECTION_NAME")

        if not all([self.uri, self.db_name, self.collection_name]):
            raise ValueError("Variables MongoDB no configuradas")

        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY no encontrada")

        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")

        # El idioma es gestionado externamente por el LanguageAgent
        self.language_detector = None
        self.session_language = None
        self.language_config = None

        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

        logger.info(f"🔗 Conectado a MongoDB: {self.db_name}.{self.collection_name}")

        self.openai_headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }

        self.openrouter_headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }

    def generate_embedding(self, text: str) -> List[float]:
        """Genera embedding usando OpenAI."""
        data = {
            "model": "text-embedding-ada-002",
            "input": text.strip()[:8000]
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=self.openai_headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def search_chunks(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Busca chunks relevantes usando similitud semántica con filtros opcionales."""
        logger.info(f"🔍 Buscando: '{query}'")
        if filters:
            logger.info(f"🎯 Aplicando filtros: {filters}")

        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []

        mongo_query = filters if filters else {}
        all_chunks = list(self.collection.find(mongo_query, {
            "content": 1,
            "document_name": 1,
            "document_title": 1,
            "section_header": 1,
            "chunk_index": 1,
            "embedding": 1,
            "program_name": 1,
            "program_full_name": 1,
            "document_category": 1,
            "target_audiences": 1
        }))

        logger.info(f"📊 Evaluando {len(all_chunks)} chunks")

        similarities = []
        for chunk in all_chunks:
            if 'embedding' in chunk and chunk['embedding']:
                similarity = self.cosine_similarity(query_embedding, chunk['embedding'])
                similarities.append({'chunk': chunk, 'similarity': similarity})

        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_chunks = similarities[:top_k]
        logger.info(f"✅ Top {len(top_chunks)} chunks encontrados")
        return top_chunks

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict:
        """Genera respuesta usando OpenAI con el idioma de sesión configurado."""
        if not self.language_config:
            self.language_config = {'code': 'es', 'name': 'Español'}

        context = "\n\n".join([
            f"**{chunk['chunk']['document_name']}** - {chunk['chunk']['section_header']}\n{chunk['chunk']['content']}"
            for chunk in context_chunks[:3]
        ])

        prompt = f"""Eres Aly, una asistente experta en programas de Equimundo. Estás aquí para ayudar a facilitadores a implementar y aplicar los programas de Equimundo.
Responde basándote exclusivamente en el contexto del manual proporcionado. Nunca inventes ni agregues información que no esté en el contexto.

## FORMATO (WhatsApp):
- *negrita* para conceptos clave y puntos importantes
- -> para listas con viñetas
- 1- para listas numeradas
- NUNCA uses barra invertida (\\) al final de una línea. Usa saltos de línea normales.
- NO uses encabezados ###.

## Tono:
- Cálido, amigable y práctico
- Valida el rol del facilitador
- Mantén las respuestas concisas y ancladas en el manual

## Restricción:
- Si la respuesta no está en el contexto, di: "No tengo información específica sobre eso. ¿Podrías reformular o preguntar algo diferente?"

## Contexto:
{context}

## Pregunta:
{query}

Respuesta:"""

        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.3
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.openai_headers,
                json=data,
                timeout=45
            )
            response.raise_for_status()
            answer_text = response.json()["choices"][0]["message"]["content"].strip()
            return {'answer': answer_text, 'language_info': self.language_config}
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            msgs = {'en': "Error generating response. Please try again.",
                    'pt': "Erro gerando resposta. Tente novamente.",
                    'es': "Error generando respuesta. Intenta de nuevo."}
            return {'answer': msgs.get(lang, msgs['es']), 'language_info': self.language_config}

    def get_stats(self):
        """Estadísticas de la base de datos."""
        stats = {}
        try:
            stats["total_chunks"] = self.collection.count_documents({})
            stats["documents"] = len(self.collection.distinct("document_name"))
            pipeline = [
                {"$group": {"_id": "$document_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            stats["documents_detail"] = list(self.collection.aggregate(pipeline))
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
        return stats
