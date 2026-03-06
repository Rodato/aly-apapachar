#!/usr/bin/env python3
"""
Ingest - Aly Apapachar
Procesa el Manual A+P (ICBF): chunking + embeddings + MongoDB.
Solo necesita ejecutarse una vez (o cuando el documento cambie).

Uso:
    python3 ingest.py
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
import requests

load_dotenv('.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ruta al documento en puddleAsistant
DOCUMENT_PATH = Path(__file__).parent.parent / "puddleAsistant" / "data" / "processed" / "DocsMD" / "3. MANUAL A+P_vICBF.docx.md"
DOCUMENT_NAME = "3. MANUAL A+P_vICBF.docx.md"

# Añadir scripts de puddleAsistant al path para usar EnhancedChunker
PUDDLE_SCRIPTS = Path(__file__).parent.parent / "puddleAsistant" / "scripts"
sys.path.insert(0, str(PUDDLE_SCRIPTS))


# ─── Embeddings ────────────────────────────────────────────────────────────────

class EmbeddingGenerator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en .env")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, text: str) -> Optional[List[float]]:
        try:
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=self.headers,
                json={"model": "text-embedding-ada-002", "input": text.strip()[:8000]},
                timeout=30
            )
            if response.status_code == 429:
                logger.warning("Rate limit — esperando 2s...")
                time.sleep(2)
                return self.generate(text)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None


# ─── MongoDB ───────────────────────────────────────────────────────────────────

class MongoUploader:
    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB_NAME")
        col_name = os.getenv("MONGODB_COLLECTION_NAME")
        if not all([uri, db_name, col_name]):
            raise ValueError("Faltan variables MongoDB en .env (MONGODB_URI, MONGODB_DB_NAME, MONGODB_COLLECTION_NAME)")
        client = MongoClient(uri)
        self.col = client[db_name][col_name]
        logger.info(f"✅ Conectado a MongoDB: {db_name}.{col_name}")

    def already_processed(self) -> bool:
        count = self.col.count_documents({"document_name": DOCUMENT_NAME})
        if count > 0:
            logger.info(f"ℹ️  El documento ya tiene {count} chunks en MongoDB.")
            return True
        return False

    def upload(self, docs: list) -> bool:
        try:
            result = self.col.insert_many(docs)
            logger.info(f"✅ {len(result.inserted_ids)} chunks insertados en MongoDB")
            return True
        except Exception as e:
            logger.error(f"❌ Error en subida: {e}")
            return False


# ─── Main ──────────────────────────────────────────────────────────────────────

def build_embedding_text(chunk) -> str:
    return "\n".join([
        f"Documento: {chunk.metadata.document_title}",
        f"Sección: {chunk.metadata.section_header}",
        f"Contenido: {chunk.content}"
    ])


def main():
    logger.info("=" * 60)
    logger.info("🚀 Aly Apapachar — Ingestión del Manual A+P (ICBF)")
    logger.info("=" * 60)

    # Verificar que el documento existe
    if not DOCUMENT_PATH.exists():
        logger.error(f"❌ Documento no encontrado: {DOCUMENT_PATH}")
        logger.error("Asegúrate de que puddleAsistant está en Desktop/Dev/ con el documento procesado.")
        sys.exit(1)

    logger.info(f"📄 Documento: {DOCUMENT_PATH.name}")

    # Conectar MongoDB
    mongo = MongoUploader()

    # Verificar si ya está procesado
    if mongo.already_processed():
        answer = input("¿Deseas reprocesar y reemplazar los chunks existentes? (s/N): ").strip().lower()
        if answer != 's':
            logger.info("Saliendo sin cambios.")
            return
        # Eliminar chunks existentes
        deleted = mongo.col.delete_many({"document_name": DOCUMENT_NAME})
        logger.info(f"🗑️  Eliminados {deleted.deleted_count} chunks anteriores")

    # Cargar EnhancedChunker de puddleAsistant
    logger.info("📦 Cargando EnhancedChunker...")
    try:
        from enhanced_chunker import EnhancedChunker
        chunker = EnhancedChunker(enable_summaries=False)
    except ImportError as e:
        logger.error(f"❌ No se pudo importar EnhancedChunker: {e}")
        logger.error(f"   Busca en: {PUDDLE_SCRIPTS}")
        sys.exit(1)

    # Generar chunks
    logger.info("✂️  Generando chunks...")
    chunks = chunker.chunk_document(DOCUMENT_PATH)
    if not chunks:
        logger.error("❌ No se generaron chunks — verifica el documento")
        sys.exit(1)
    logger.info(f"✅ {len(chunks)} chunks generados")

    # Generar embeddings
    embedder = EmbeddingGenerator()
    logger.info(f"🔢 Generando embeddings para {len(chunks)} chunks (puede tardar ~{len(chunks)*0.15:.0f}s)...")

    mongo_docs = []
    for i, chunk in enumerate(chunks):
        if i % 10 == 0:
            logger.info(f"   Chunk {i+1}/{len(chunks)}...")

        emb_text = build_embedding_text(chunk)
        embedding = embedder.generate(emb_text)

        if not embedding:
            logger.warning(f"⚠️  Chunk {i} sin embedding — saltando")
            continue

        meta = chunk.metadata
        mongo_docs.append({
            "document_name":    DOCUMENT_NAME,
            "chunk_id":         meta.chunk_id,
            "chunk_index":      meta.chunk_index,
            "document_source":  meta.document_source,
            "document_title":   meta.document_title,
            "document_type":    meta.document_type,
            "content":          chunk.content,
            "section_header":   meta.section_header,
            "content_type":     meta.content_type,
            "text_length":      meta.text_length,
            "word_count":       meta.word_count,
            "total_chunks":     meta.total_chunks,
            "embedding":        embedding,
            "embedding_text":   emb_text,
            "embedding_model":  "text-embedding-ada-002",
            "has_code":         meta.has_code,
            "has_numbers":      meta.has_numbers,
            "has_bullets":      meta.has_bullets,
            "has_tables":       meta.has_tables,
            "has_images":       meta.has_images,
            "parent_section":   meta.parent_section,
            "processed_at":     meta.processed_at,
            "chunk_hash":       meta.chunk_hash,
        })

        time.sleep(0.1)  # Evitar rate limit

    logger.info(f"✅ {len(mongo_docs)} embeddings generados de {len(chunks)} chunks")

    # Subir a MongoDB
    logger.info("📤 Subiendo a MongoDB...")
    success = mongo.upload(mongo_docs)

    if success:
        # Guardar backup local
        backup_dir = Path("data")
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / "apapachar_embeddings_backup.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            # No guardar los embeddings completos (muy pesados), solo metadatos
            backup_data = [{k: str(v) if hasattr(v, '__class__') and v.__class__.__name__ == 'ObjectId' else v
                        for k, v in d.items() if k != 'embedding'} for d in mongo_docs]
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Backup de metadatos guardado en {backup_file}")

        logger.info("")
        logger.info("🎉 ¡Ingestión completada!")
        logger.info(f"   📄 Documento: {DOCUMENT_NAME}")
        logger.info(f"   📝 Chunks en MongoDB: {len(mongo_docs)}")
        logger.info("")
        logger.info("Ahora puedes probar con: python3 console.py")
    else:
        logger.error("❌ Error en la subida — revisa los logs")
        sys.exit(1)


if __name__ == "__main__":
    main()
