#!/usr/bin/env python3
"""
Orchestrator - Aly Apapachar
Flujo: Language → Intent → {GREETING | FACTUAL | PLAN | IDEATE | SENSITIVE}
"""

import logging
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

from agents.base_agent import AgentState
from agents.language_agent import LanguageAgent
from agents.intent_agent import IntentAgent
from agents.rag_agent import ApapacharRAGAgent
from agents.plan_agent import PlanAgent
from agents.ideate_agent import IdeateAgent
from config.welcome_messages import get_welcome_message, get_sensitive_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    user_input: str
    language: str
    language_config: Dict
    mode: str
    mode_confidence: float
    response: str
    sources: list
    debug_info: Dict


class ApapacharOrchestrator:
    """
    Orquestador para Aly Apapachar.
    Fuente única: Manual A+P (ICBF).
    Agentes: FACTUAL (gpt-4o-mini) | PLAN (gemini-2.5-flash-lite) | IDEATE (mistral-small-creative)
    """

    def __init__(self):
        self.language_agent = LanguageAgent()
        self.intent_agent = IntentAgent()
        self.rag_agent = ApapacharRAGAgent()
        self.plan_agent = PlanAgent()
        self.ideate_agent = IdeateAgent()

        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        logger.info("✅ Apapachar Orchestrator inicializado (FACTUAL + PLAN + IDEATE)")

    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(GraphState)

        workflow.add_node("detect_language", self._language_node)
        workflow.add_node("detect_intent", self._intent_node)
        workflow.add_node("greeting_response", self._greeting_node)
        workflow.add_node("factual_response", self._factual_node)
        workflow.add_node("plan_response", self._plan_node)
        workflow.add_node("ideate_response", self._ideate_node)
        workflow.add_node("sensitive_response", self._sensitive_node)

        workflow.set_entry_point("detect_language")
        workflow.add_edge("detect_language", "detect_intent")
        workflow.add_conditional_edges(
            "detect_intent",
            self._route,
            {
                "GREETING":  "greeting_response",
                "FACTUAL":   "factual_response",
                "PLAN":      "plan_response",
                "IDEATE":    "ideate_response",
                "SENSITIVE": "sensitive_response"
            }
        )
        for node in ("greeting_response", "factual_response", "plan_response", "ideate_response", "sensitive_response"):
            workflow.add_edge(node, END)

        return workflow

    # ── Nodos ────────────────────────────────────────────────────────────────

    def _language_node(self, state: GraphState) -> GraphState:
        agent_state = AgentState(user_input=state["user_input"])
        result = self.language_agent.process(agent_state)
        return {**state, "language": result.language, "language_config": result.language_config, "debug_info": {}}

    def _intent_node(self, state: GraphState) -> GraphState:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"]
        )
        result = self.intent_agent.process(agent_state)
        return {**state, "mode": result.mode, "mode_confidence": result.mode_confidence}

    def _greeting_node(self, state: GraphState) -> GraphState:
        welcome = get_welcome_message(state.get("language", "es"))
        logger.info(f"👋 GREETING → bienvenida en {state.get('language', 'es')}")
        return {**state, "response": welcome, "sources": []}

    def _factual_node(self, state: GraphState) -> GraphState:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode="FACTUAL"
        )
        result = self.rag_agent.process(agent_state)
        return {**state, "response": result.response, "sources": result.sources or []}

    def _plan_node(self, state: GraphState) -> GraphState:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode="PLAN"
        )
        result = self.plan_agent.process(agent_state)
        return {**state, "response": result.response, "sources": result.sources or []}

    def _ideate_node(self, state: GraphState) -> GraphState:
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode="IDEATE"
        )
        result = self.ideate_agent.process(agent_state)
        return {**state, "response": result.response, "sources": result.sources or []}

    def _sensitive_node(self, state: GraphState) -> GraphState:
        msg = get_sensitive_message(state.get("language", "es"))
        logger.info("⚠️ SENSITIVE → respuesta de derivación")
        return {**state, "response": msg, "sources": []}

    def _route(self, state: GraphState) -> str:
        return state.get("mode", "FACTUAL")

    # ── API pública ───────────────────────────────────────────────────────────

    def process_query(self, user_input: str) -> Dict[str, Any]:
        logger.info(f"🤖 Procesando: '{user_input[:60]}...'")

        initial_state = {
            "user_input": user_input,
            "language": None,
            "language_config": {},
            "mode": None,
            "mode_confidence": 0.0,
            "response": "",
            "sources": [],
            "debug_info": {}
        }

        try:
            final_state = self.app.invoke(initial_state)
            return {
                "query": user_input,
                "answer": final_state["response"],
                "intent": final_state["mode"],
                "language": final_state["language"],
                "language_detected": final_state["language"],
                "sources": final_state["sources"]
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
