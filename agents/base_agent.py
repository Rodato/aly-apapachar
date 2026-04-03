#!/usr/bin/env python3
"""
Base Agent - Aly Apapachar
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Estado compartido entre agentes."""
    user_input: str
    language: Optional[str] = None
    language_config: Optional[Dict] = None
    mode: Optional[str] = None
    mode_confidence: Optional[float] = None
    response: Optional[str] = None
    sources: Optional[list] = None
    debug_info: Optional[Dict] = None
    # User profile from MongoDB (set by bot.py before entering orchestrator)
    user_profile: Optional[Dict] = None
    # Collections to query — set by LibrarianAgent
    sources_to_query: Optional[List[str]] = None
    # Metadata filters per collection — set by LibrarianAgent
    # e.g. {"aly_general_knowledge": {"theme_category": ["rompehielos"]}}
    rag_filters: Optional[Dict] = None

class BaseAgent(ABC):
    """Agente base con funcionalidades comunes."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        pass

    def log_processing(self, state: AgentState, action: str):
        self.logger.info(f"🤖 {self.name}: {action}")

    def add_debug_info(self, state: AgentState, key: str, value: Any):
        if state.debug_info is None:
            state.debug_info = {}
        if self.name not in state.debug_info:
            state.debug_info[self.name] = {}
        state.debug_info[self.name][key] = value
