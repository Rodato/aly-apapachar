"""
OnboardingAgent — flujo de registro de nuevos facilitadores.

Diseño stateless: cada llamada lee el estado actual del perfil desde MongoDB,
procesa el input del usuario para ese paso, actualiza MongoDB y devuelve la
siguiente pregunta. No hay sesión en memoria.
"""

import logging
from typing import Dict, Optional

from agents.base_agent import BaseAgent, AgentState
from db.user_profiles import update_onboarding_field

logger = logging.getLogger(__name__)


# Opciones de regiones para Colombia (según diagrama de onboarding)
COLOMBIA_REGIONS = [
    "Boyacá",
    "Caquetá",
    "Meta",
    "Cundinamarca",
    "Chocó",
    "Huila",
    "Magdalena",
    "Santander",
    "Sucre",
    "Tolima",
]

REGION_LIST = "\n".join(f"{i+1}. {r}" for i, r in enumerate(COLOMBIA_REGIONS))

QUESTIONS = {
    "awaiting_name": (
        "¡Hola! Soy Aly, tu asistente de Equimundo. "
        "Me encantaría conocerte un poco para poder ayudarte mejor. "
        "¿Cuál es tu nombre y apellido?"
    ),
    "awaiting_gender": "¿Cómo te identificas?\n1. Hombre\n2. Mujer\n3. Otro",
    "awaiting_country": "¿Dónde estás?\n1. Colombia 🇨🇴\n2. México 🇲🇽\n3. Otro 🌍",
    "awaiting_region": f"¿En qué región de Colombia estás?\n{REGION_LIST}",
    "awaiting_email": (
        "Por último, ¿cuál es tu correo electrónico?\n"
        "(Lo usamos únicamente para mejorar la herramienta. "
        "No compartiremos esta información con nadie 🤝)"
    ),
}

GENDER_MAP = {
    "1": "hombre", "hombre": "hombre",
    "2": "mujer",  "mujer": "mujer",
    "3": "otro",   "otro": "otro",
}

COUNTRY_MAP = {
    "1": "colombia", "colombia": "colombia",
    "2": "mexico",   "méxico": "colombia", "mexico": "mexico",
    "3": "otro",     "otro": "otro",
}


class OnboardingAgent(BaseAgent):

    def __init__(self):
        super().__init__("OnboardingAgent", "Gestiona el registro inicial del facilitador")

    def process(self, state: AgentState) -> AgentState:
        profile = state.user_profile
        if not profile:
            state.response = QUESTIONS["awaiting_name"]
            return state

        current_step = profile.get("onboarding_state", "awaiting_name")
        user_input = (state.user_input or "").strip()

        handler = {
            "awaiting_name":    self._handle_name,
            "awaiting_gender":  self._handle_gender,
            "awaiting_country": self._handle_country,
            "awaiting_region":  self._handle_region,
            "awaiting_email":   self._handle_email,
        }.get(current_step)

        if handler:
            state.response = handler(profile, user_input)
        else:
            # Should not happen — but fallback to first question
            state.response = QUESTIONS["awaiting_name"]

        return state

    # ------------------------------------------------------------------
    # Step handlers — each returns the response string
    # ------------------------------------------------------------------

    def _handle_name(self, profile: Dict, user_input: str) -> str:
        if not user_input:
            return QUESTIONS["awaiting_name"]
        name = user_input.title()
        update_onboarding_field(profile["whatsapp_number"], "name", name, "awaiting_gender")
        return f"Gracias, {name}. {QUESTIONS['awaiting_gender']}"

    def _handle_gender(self, profile: Dict, user_input: str) -> str:
        normalized = GENDER_MAP.get(user_input.lower())
        if not normalized:
            return f"Por favor elige una opción válida.\n{QUESTIONS['awaiting_gender']}"
        update_onboarding_field(profile["whatsapp_number"], "gender_identity", normalized, "awaiting_country")
        return QUESTIONS["awaiting_country"]

    def _handle_country(self, profile: Dict, user_input: str) -> str:
        normalized = COUNTRY_MAP.get(user_input.lower())
        if not normalized:
            return f"Por favor elige una opción válida.\n{QUESTIONS['awaiting_country']}"

        if normalized == "colombia":
            update_onboarding_field(profile["whatsapp_number"], "country", normalized, "awaiting_region")
            return QUESTIONS["awaiting_region"]
        else:
            # Skip region for non-Colombia users — two atomic updates
            update_onboarding_field(profile["whatsapp_number"], "country", normalized, "awaiting_email")
            return QUESTIONS["awaiting_email"]

    def _handle_region(self, profile: Dict, user_input: str) -> str:
        region = self._parse_region(user_input)
        if not region:
            return f"Por favor elige una región válida.\n{QUESTIONS['awaiting_region']}"
        update_onboarding_field(profile["whatsapp_number"], "region", region, "awaiting_email")
        return QUESTIONS["awaiting_email"]

    def _handle_email(self, profile: Dict, user_input: str) -> str:
        if "@" not in user_input or "." not in user_input:
            return "Parece que ese correo no es válido. ¿Puedes escribirlo de nuevo?"
        update_onboarding_field(profile["whatsapp_number"], "email", user_input.lower().strip(), "complete")
        name = profile.get("name") or "Facilitador"
        return (
            f"¡Listo, {name}! Ya estás registrado. "
            "¿En qué puedo ayudarte hoy? 🌟\n\n"
            "Aquí tienes algunas formas en las que puedo ayudarte: "
            "planear una sesión, adaptar una actividad, hacer una pregunta difícil, "
            "resolver un desafío complejo u obtener ideas para involucrar a los participantes.\n\n"
            "_Aly está entrenada con la metodología de Equimundo y diseñada para apoyar a facilitadores como tú._"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_region(self, user_input: str) -> Optional[str]:
        """Acepta número (1-10) o nombre de región (case-insensitive)."""
        text = user_input.strip()
        # Try numeric
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(COLOMBIA_REGIONS):
                return COLOMBIA_REGIONS[idx]
            return None
        # Try name match
        for region in COLOMBIA_REGIONS:
            if region.lower() == text.lower():
                return region
        return None
