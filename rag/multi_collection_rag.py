"""
MultiCollectionRAG — busca en múltiples colecciones MongoDB y fusiona resultados.
No modifica SimpleMongoRAG (backward compatibility).
"""

import os
import logging
from typing import List, Dict, Optional

import numpy as np
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class MultiCollectionRAG:
    """
    RAG que soporta múltiples colecciones MongoDB.
    Fusiona resultados por similitud coseno y permite usar subsets de colecciones por request.
    """

    def __init__(self, collection_names: List[str]):
        """
        collection_names: lista de colecciones a tener disponibles.
        e.g. ["apapachar", "aly_general_knowledge"]
        Todas deben estar en la misma DB (MONGODB_DB_NAME).
        """
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        if not all([self.uri, self.db_name, self.openai_key]):
            raise ValueError("MONGODB_URI, MONGODB_DB_NAME y OPENAI_API_KEY son requeridas")

        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collections = {name: self.db[name] for name in collection_names}

        self.openai_headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"🔗 MultiCollectionRAG conectado a: {list(self.collections.keys())}")

    # ------------------------------------------------------------------
    # Core search
    # ------------------------------------------------------------------

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        try:
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=self.openai_headers,
                json={"model": "text-embedding-ada-002", "input": text.strip()[:8000]},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2))

    def search_chunks(
        self,
        query: str,
        top_k: int = 5,
        collections_to_use: Optional[List[str]] = None,
        metadata_filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Busca en el subset indicado de colecciones.
        Retorna lista fusionada de chunks ordenados por similitud, cada uno con campo 'collection'.

        collections_to_use: subset de self.collections a usar.
            Si es None, usa todas las colecciones disponibles.
        metadata_filters: filtros de metadata por colección.
            e.g. {"aly_general_knowledge": {"theme_category": ["rompehielos", "tips_facilitadores"]}}
            Solo aplica a colecciones que soporten metadata estructurada (aly_general_knowledge).
            Si el filtro retorna 0 documentos, hace fallback sin filtro.
        """
        active_cols = collections_to_use or list(self.collections.keys())
        # Validate — silently ignore unknown names
        active_cols = [c for c in active_cols if c in self.collections]
        if not active_cols:
            logger.warning("No valid collections to search")
            return []

        logger.info(f"🔍 MultiRAG buscando en {active_cols}: '{query[:60]}'")
        if metadata_filters:
            logger.info(f"   Filtros de metadata: {metadata_filters}")

        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []

        all_similarities = []

        for col_name in active_cols:
            col = self.collections[col_name]

            # Build MongoDB query from metadata_filters for this collection
            mongo_query = {}
            if metadata_filters and col_name in metadata_filters:
                for field, values in metadata_filters[col_name].items():
                    if isinstance(values, list):
                        mongo_query[field] = {"$in": values}
                    else:
                        mongo_query[field] = values

            projection = {
                "content": 1,
                "document_name": 1,
                "section_header": 1,
                "theme_category": 1,
                "chunk_index": 1,
                "embedding": 1,
                "keywords": 1,
            }

            chunks = list(col.find(mongo_query, projection))

            # Fallback: if metadata filter returned 0 docs, retry without filter
            if mongo_query and not chunks:
                logger.warning(f"   {col_name}: filtro de metadata sin resultados — fallback sin filtro")
                chunks = list(col.find({}, projection))

            logger.info(f"   {col_name}: {len(chunks)} chunks evaluados")

            for chunk in chunks:
                if chunk.get("embedding"):
                    sim = self.cosine_similarity(query_embedding, chunk["embedding"])
                    all_similarities.append({
                        "chunk": chunk,
                        "similarity": sim,
                        "collection": col_name,
                    })

        all_similarities.sort(key=lambda x: x["similarity"], reverse=True)
        top = all_similarities[:top_k]
        logger.info(f"✅ Top {len(top)} chunks (merged from {active_cols})")
        return top
