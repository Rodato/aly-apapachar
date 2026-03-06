#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv('.env')
from pymongo import MongoClient

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB_NAME')]
col = db[os.getenv('MONGODB_COLLECTION_NAME')]

query = {"document_name": {"$regex": "MANUAL A\\+P_vICBF", "$options": "i"}}
count = col.count_documents(query)
print(f"Chunks encontrados para A+P vICBF: {count}")

if count > 0:
    sample = col.find_one(query)
    print(f"document_name: {sample['document_name']}")
    print(f"tiene embedding: {'embedding' in sample and len(sample['embedding']) > 0}")
    print(f"total chunks en colección: {col.count_documents({})}")
else:
    print("El documento NO está en MongoDB todavía — hay que procesarlo.")
    # Listar documentos únicos disponibles
    docs = col.distinct("document_name")
    print(f"\nDocumentos en MongoDB ({len(docs)}):")
    for d in sorted(docs):
        print(f"  - {d}")
