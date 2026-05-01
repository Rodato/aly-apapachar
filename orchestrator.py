#!/usr/bin/env python3
"""
Orchestrator - Aly Equimundo
Flujo: triage → SENSITIVE: sensitive_response
               CONTINUE:   Language → [Intent + Librarian en paralelo] → barrier → {GREETING | FACTUAL | PLAN | IDEATE}
Cada agente de respuesta (Factual, Plan, Ideate) recupera y genera su propio contexto.
"""

import logging
import requests as _requests
from typing import Annotated, Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END

from agents.base_agent import AgentState
from agents.language_agent import LanguageAgent
from agents.intent_agent import IntentAgent
from agents.librarian_agent import LibrarianAgent
from agents.factual_agent import FactualAgent
from agents.plan_agent import PlanAgent
from agents.ideate_agent import IdeateAgent
from agents.sensitive_agent import SensitiveAgent
from config.welcome_messages import get_welcome_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _last_wins(a, b):
    """Reducer para campos escritos por ramas paralelas: la última escritura gana."""
    return b


class GraphState(TypedDict):
    user_input: str
    language: str
    language_config: Dict
    # Escrito por detect_intent (rama paralela) → necesita reducer
    mode: Annotated[str, _last_wins]
    mode_confidence: Annotated[float, _last_wins]
    response: str
    sources: list
    debug_info: Dict
    user_profile: Dict
    # Escritos por librarian (rama paralela) → necesitan reducer
    sources_to_query: Annotated[List[str], _last_wins]
    rag_filters: Annotated[Optional[Dict], _last_wins]


class ApapacharOrchestrator:
    """
    Orquestador para Aly Equimundo.
    Intent Agent y Librarian Agent corren en paralelo tras detectar el idioma.
    Cada agente de respuesta (Factual, Plan, Ideate) hace su propia recuperación RAG
    usando las colecciones y filtros decididos por el Librarian.
    """

    def __init__(self):
        self.language_agent = LanguageAgent()
        self.intent_agent = IntentAgent()
        self.librarian_agent = LibrarianAgent()
        self.factual_agent = FactualAgent()
        self.plan_agent = PlanAgent()
        self.ideate_agent = IdeateAgent()
        self.sensitive_agent = SensitiveAgent()

        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        logger.info("✅ Equimundo Orchestrator inicializado (parallel Intent + Librarian)")

    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(GraphState)

        workflow.add_node("triage", self._triage_node)
        workflow.add_node("detect_language", self._language_node)
        workflow.add_node("detect_intent", self._intent_node)
        workflow.add_node("librarian", self._librarian_node)
        workflow.add_node("barrier", self._barrier_node)
        workflow.add_node("greeting_response", self._greeting_node)
        workflow.add_node("factual_response", self._factual_node)
        workflow.add_node("plan_response", self._plan_node)
        workflow.add_node("ideate_response", self._ideate_node)
        workflow.add_node("sensitive_response", self._sensitive_node)

        workflow.set_entry_point("triage")

        # Triage: SENSITIVE directo, cualquier otra cosa sigue el flujo normal
        workflow.add_conditional_edges(
            "triage",
            self._route_after_triage,
            {
                "SENSITIVE": "sensitive_response",
                "CONTINUE":  "detect_language",
            }
        )

        # Fan-out paralelo: detect_language → detect_intent Y librarian simultáneamente
        workflow.add_edge("detect_language", "detect_intent")
        workflow.add_edge("detect_language", "librarian")

        # Ambas ramas convergen en barrier
        workflow.add_edge("detect_intent", "barrier")
        workflow.add_edge("librarian", "barrier")

        # Barrier → routing al agente de respuesta (SENSITIVE ya no llega aquí)
        workflow.add_conditional_edges(
            "barrier",
            self._route_after_barrier,
            {
                "GREETING": "greeting_response",
                "FACTUAL":  "factual_response",
                "PLAN":     "plan_response",
                "IDEATE":   "ideate_response",
            }
        )

        for node in ("greeting_response", "factual_response", "plan_response",
                     "ideate_response", "sensitive_response"):
            workflow.add_edge(node, END)

        return workflow

    # ── Nodos ────────────────────────────────────────────────────────────────

    def _triage_node(self, state: GraphState) -> dict:
        """Filtro rápido: ¿es SENSITIVE? Si sí, saltea Language + Librarian."""
        user_input = state["user_input"]
        is_sensitive = self._is_sensitive(user_input)
        if is_sensitive:
            logger.info("⚠️ TRIAGE → SENSITIVE detectado, saltando Language + Librarian")
            return {"mode": "SENSITIVE"}
        logger.info("✅ TRIAGE → no sensible, flujo normal")
        return {"user_input": state["user_input"]}

    def _is_sensitive(self, user_input: str) -> bool:
        prompt = f"""Eres un clasificador para Aly, asistente de facilitadores de Equimundo.

Determina si este mensaje requiere una respuesta SENSIBLE.

Es SENSITIVE si:
- El/la facilitador/a reporta o vive angustia emocional propia ("me afectó mucho", "no sé cómo manejarlo, me desbordó")
- Un participante divulgó una situación de violencia, abuso o riesgo ("me contó que su pareja lo golpea")
- Hay una crisis activa o riesgo inminente para alguien
- El mensaje contiene daño normativo: chistes sexistas, minimización de violencia, estereotipos dañinos ("fue solo un chiste", "algo habrá hecho")

NO es SENSITIVE si pregunta sobre temas difíciles desde un lugar informativo o de planificación — aunque el tema sea violencia, abuso o género.

Ejemplos:
"me afectó mucho lo que pasó en la sesión de hoy" → SENSITIVE
"un participante me contó que su pareja lo golpea" → SENSITIVE
"alguien hizo un chiste sobre violación y el grupo se rió" → SENSITIVE
"tengo miedo de perder el control con mi pareja" → SENSITIVE
"¿cómo hablo del ciclo de violencia en la sesión 4?" → NOT_SENSITIVE
"dame ideas para la actividad de masculinidades" → NOT_SENSITIVE
"¿qué dice Apapáchar sobre paternidad activa?" → NOT_SENSITIVE

Mensaje: "{user_input}"

Responde SOLO con una palabra: SENSITIVE o NOT_SENSITIVE"""

        try:
            resp = _requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.intent_agent.headers,
                json={
                    "model": "mistralai/ministral-8b-2512",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0.0,
                },
                timeout=15,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip().upper()
            return "SENSITIVE" in content and "NOT_SENSITIVE" not in content
        except Exception as e:
            logger.error(f"❌ Error en triage, continuando flujo normal: {e}")
            return False  # failsafe: flujo normal

    def _route_after_triage(self, state: GraphState) -> str:
        return "SENSITIVE" if state.get("mode") == "SENSITIVE" else "CONTINUE"

    def _language_node(self, state: GraphState) -> dict:
        agent_state = AgentState(user_input=state["user_input"])
        result = self.language_agent.process(agent_state)
        return {
            "language": result.language,
            "language_config": result.language_config,
            "debug_info": {},
        }

    def _intent_node(self, state: GraphState) -> dict:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
        )
        result = self.intent_agent.process(agent_state)
        return {"mode": result.mode, "mode_confidence": result.mode_confidence}

    def _librarian_node(self, state: GraphState) -> dict:
        agent_state = AgentState(
            user_input=state["user_input"],
            user_profile=state.get("user_profile") or {},
        )
        result = self.librarian_agent.process(agent_state)
        return {
            "sources_to_query": result.sources_to_query or ["apapachar"],
            "rag_filters": result.rag_filters,
        }

    def _barrier_node(self, state: GraphState) -> dict:
        """Nodo de sincronización — espera que detect_intent y librarian completen."""
        logger.info(
            f"⚡ Barrier — mode={state.get('mode')} "
            f"sources={state.get('sources_to_query')} "
            f"filters={state.get('rag_filters')}"
        )
        return {"user_input": state["user_input"]}

    def _greeting_node(self, state: GraphState) -> dict:
        welcome = get_welcome_message(state.get("language", "es"))
        logger.info(f"👋 GREETING → bienvenida en {state.get('language', 'es')}")
        return {"response": welcome, "sources": []}

    def _factual_node(self, state: GraphState) -> dict:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode="FACTUAL",
            user_profile=state.get("user_profile"),
            sources_to_query=state.get("sources_to_query"),
            rag_filters=state.get("rag_filters"),
        )
        result = self.factual_agent.process(agent_state)
        return {"response": result.response, "sources": result.sources or []}

    def _plan_node(self, state: GraphState) -> dict:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode="PLAN",
            user_profile=state.get("user_profile"),
            sources_to_query=state.get("sources_to_query"),
            rag_filters=state.get("rag_filters"),
        )
        result = self.plan_agent.process(agent_state)
        return {"response": result.response, "sources": result.sources or []}

    def _ideate_node(self, state: GraphState) -> dict:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode="IDEATE",
            user_profile=state.get("user_profile"),
            sources_to_query=state.get("sources_to_query"),
            rag_filters=state.get("rag_filters"),
        )
        result = self.ideate_agent.process(agent_state)
        return {"response": result.response, "sources": result.sources or []}

    def _sensitive_node(self, state: GraphState) -> dict:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state.get("language") or "es",
            language_config=state.get("language_config") or {"code": "es"},
            mode="SENSITIVE",
        )
        result = self.sensitive_agent.process(agent_state)
        logger.info("⚠️ SENSITIVE → respuesta generada por SensitiveAgent")
        return {"response": result.response, "sources": []}

    # ── Routing ───────────────────────────────────────────────────────────────

    def _route_after_barrier(self, state: GraphState) -> str:
        return state.get("mode", "FACTUAL")

    # ── API pública ───────────────────────────────────────────────────────────

    def process_query(self, user_input: str, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        logger.info(f"🤖 Procesando: '{user_input[:60]}...'")

        initial_state = {
            "user_input": user_input,
            "language": None,
            "language_config": {},
            "mode": None,
            "mode_confidence": 0.0,
            "response": "",
            "sources": [],
            "debug_info": {},
            "user_profile": user_profile or {},
            "sources_to_query": [],
            "rag_filters": None,
        }

        try:
            final_state = self.app.invoke(initial_state)
            return {
                "query": user_input,
                "answer": final_state["response"],
                "intent": final_state["mode"],
                "language": final_state["language"],
                "language_detected": final_state["language"],
                "sources": final_state["sources"],
                "sources_queried": final_state.get("sources_to_query", []),
            }
        except Exception as e:
            logger.error(f"❌ Error en orchestrator: {e}")
            return {
                "query": user_input,
                "answer": "Error procesando tu consulta. Intenta de nuevo.",
                "intent": "error",
                "language": "es",
                "language_detected": "es",
                "sources": [],
                "error": str(e)
            }
