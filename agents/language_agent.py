#!/usr/bin/env python3
"""
Language Agent - Aly Apapachar
Detecta el idioma del usuario (ES/EN/PT)
"""

import os
import sys
from typing import Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_detector import LLMLanguageDetector
from .base_agent import BaseAgent, AgentState


class LanguageAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="language_agent",
            description="Detecta el idioma del usuario (ES/EN/PT)"
        )
        try:
            self.language_detector = LLMLanguageDetector()
            self.logger.info("✅ Language detector inicializado")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando detector: {e}")
            self.language_detector = None

    def process(self, state: AgentState) -> AgentState:
        if state.language is not None:
            return state

        self.log_processing(state, f"Detectando idioma: '{state.user_input[:50]}...'")

        if self.language_detector:
            try:
                language_config = self.language_detector.get_language_config(state.user_input)
                state.language = language_config['code']
                state.language_config = language_config
                self.log_processing(state, f"Idioma: {language_config['name']}")
                return state
            except Exception as e:
                self.logger.error(f"❌ Error detectando idioma: {e}")

        # Fallback
        state.language = 'es'
        state.language_config = {
            'code': 'es',
            'name': 'Español',
            'greeting': '¡Hola! Soy Aly. ¿Cómo puedo ayudarte hoy?',
            'no_context': 'No encontré información relevante para tu pregunta.',
            'response_instruction': 'Responde en español.',
            'context_instruction': 'Responde basándote en el contexto proporcionado en español.',
        }
        return state
