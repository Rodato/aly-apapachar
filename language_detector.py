#!/usr/bin/env python3
"""
Language Detector - Aly Apapachar
Copia directa de puddleAsistant/mvp/language_detector.py
"""

import os
import json
import logging
from typing import Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMLanguageDetector:
    """Detector de idioma español/inglés/portugués usando LLM."""

    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada en .env")

        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "mistralai/ministral-8b-2512"
        logger.info("✅ LLM Language Detector inicializado (ES/EN/PT)")

    def detect_language(self, text: str) -> Dict:
        if not text or len(text.strip()) < 2:
            return {'language': 'spanish', 'confidence': 0.5, 'reasoning': 'Texto muy corto'}

        prompt = f"""Analiza el siguiente texto y determina si está escrito en español, inglés o portugués.

Texto: "{text}"

Responde SOLO con un JSON válido en este formato exacto:
{{
    "language": "spanish" o "english" o "portuguese",
    "confidence": 0.0-1.0,
    "reasoning": "breve explicación"
}}

Reglas:
- Si hay mezcla de idiomas, elige el dominante
- Si es ambiguo, usa "spanish" como default
- Portuguese se diferencia del español por: ção, não, muito, fazer, etc."""

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.1
                },
                timeout=30
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            return self._parse_llm_response(content)
        except Exception as e:
            logger.error(f"Error en detección LLM: {e}")
            return self._simple_fallback(text)

    def _parse_llm_response(self, content: str) -> Dict:
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                parsed = json.loads(content[start:end])
                if 'language' in parsed and parsed['language'] in ('spanish', 'english', 'portuguese'):
                    return {
                        'language': parsed['language'],
                        'confidence': float(parsed.get('confidence', 0.8)),
                        'reasoning': parsed.get('reasoning', 'Análisis LLM')
                    }
        except Exception:
            pass

        lower = content.lower()
        if 'portuguese' in lower:
            return {'language': 'portuguese', 'confidence': 0.7, 'reasoning': 'Detectado en texto'}
        if 'english' in lower:
            return {'language': 'english', 'confidence': 0.7, 'reasoning': 'Detectado en texto'}
        return {'language': 'spanish', 'confidence': 0.5, 'reasoning': 'Default fallback'}

    def _simple_fallback(self, text: str) -> Dict:
        lower = text.lower()
        pt = sum(1 for w in ['não', 'ção', 'muito', 'você', 'fazer'] if w in lower)
        es = sum(1 for w in ['qué', 'cómo', '¿', '¡', 'también', 'año'] if w in lower)
        en = sum(1 for w in ['what', 'how', 'the ', ' and ', ' you '] if w in lower)
        if pt >= es and pt >= en and pt > 0:
            return {'language': 'portuguese', 'confidence': 0.6, 'reasoning': 'Fallback keywords'}
        if en > es and en > 0:
            return {'language': 'english', 'confidence': 0.6, 'reasoning': 'Fallback keywords'}
        return {'language': 'spanish', 'confidence': 0.6, 'reasoning': 'Fallback default'}

    def get_response_language(self, text: str) -> str:
        result = self.detect_language(text)
        if result['language'] == 'english':
            return 'en'
        if result['language'] == 'portuguese':
            return 'pt'
        return 'es'

    def get_language_config(self, text: str) -> Dict:
        lang = self.get_response_language(text)
        configs = {
            'en': {
                'code': 'en', 'name': 'English',
                'response_instruction': 'Respond in English.',
                'context_instruction': 'Answer based on the provided context in English.',
                'greeting': "Hi! I'm Aly. How can I help you with the A+P program today?",
                'no_context': "I couldn't find relevant information for your question."
            },
            'pt': {
                'code': 'pt', 'name': 'Português',
                'response_instruction': 'Responda em português.',
                'context_instruction': 'Responda baseado no contexto fornecido em português.',
                'greeting': "Olá! Sou Aly. Como posso ajudá-lo com o programa A+P hoje?",
                'no_context': "Não encontrei informações relevantes para sua pergunta."
            },
            'es': {
                'code': 'es', 'name': 'Español',
                'response_instruction': 'Responde en español.',
                'context_instruction': 'Responde basándote en el contexto proporcionado en español.',
                'greeting': '¡Hola! Soy Aly. ¿Cómo puedo ayudarte con el programa A+P hoy?',
                'no_context': 'No encontré información relevante para tu pregunta.'
            }
        }
        return configs.get(lang, configs['es'])
