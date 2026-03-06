# src/agents/python_agent/agent.py
from src.base_workflows.base_coding_agent_workflow.agent import BaseCodingAgent
from src.base_workflows.base_coding_agent_workflow.state import BaseAgentState, BaseFileAgentState
from .nodes.planner import planner_node
from .nodes.coder import coder_node
from .nodes.reviewer import reviewer_node
from .nodes.static_check import static_check_node


class PythonCodingAgent(BaseCodingAgent):
    """
    Python-specific coding agent.
    Uses ruff for static analysis, Python-specific prompts.
    Only overrides language-specific nodes.
    """

    def planner_node(self, state: BaseAgentState) -> BaseAgentState:
        return planner_node(state)          # python-specific planner

    def coder_node(self, state: BaseFileAgentState) -> BaseFileAgentState:
        return coder_node(state)            # python-specific coder

    def reviewer_node(self, state: BaseFileAgentState) -> BaseFileAgentState:
        return reviewer_node(state)         # python-specific reviewer

    def static_check_node(self, state: BaseFileAgentState) -> BaseFileAgentState:
        return static_check_node(state)     # ruff-specifics