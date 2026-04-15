"""
Agent Task Execution Module.

This module provides a command-line interface to execute coding tasks using specialized agents.
It supports multiple programming languages through a pluggable agent architecture, allowing
tasks to be processed by language-specific agents (e.g., Python, JavaScript).

The module can be used programmatically via the run() function or as a standalone CLI script
through the __main__ entry point.
"""

from typing import Type, Dict, Any

from src.agents.python_coding_agent.agent import PythonCodingAgent


# Mapping of supported programming languages to their corresponding agent classes
# Enables language-based agent selection for task execution
AGENTS: Dict[str, Type] = {
    "python": PythonCodingAgent,  # Python coding tasks handled by PythonCodingAgent
    # "javascript": JavaScriptCodingAgent,  # TODO: JavaScript support (pending implementation)
}


def run(task: str, language: str = "python") -> Any:
    """
    Execute a coding task using the specified language agent.

    Dispatches the provided task to the appropriate agent based on the specified programming
    language. The agent processes the task and returns the execution result.

    Args:
        task (str): The description or specification of the coding task to execute.
            Can be a text prompt or specification describing the desired code generation.
        language (str, optional): The programming language for the task. Defaults to "python".
            Must be a key in the AGENTS mapping. Supported values: "python".

    Returns:
        Any: The execution result from the selected agent. Return type depends on the specific
            agent implementation.

    Raises:
        ValueError: If the specified language is not supported (not in AGENTS dictionary).

    Example:
        >>> result = run("Create a FastAPI endpoint for user management")
        >>> result = run("Write a React component", language="javascript")

    # Note: Original signature with work_dir and execution_id parameters:
    # def run(task: str, work_dir: str, language: str = "python", execution_id: int = 4)
    """
    # Retrieve the agent class corresponding to the requested language
    agent_cls: Type = AGENTS.get(language)

    # Validate that the specified language is supported
    if not agent_cls:
        supported_languages: list = list(AGENTS.keys())
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Choose from {supported_languages}"
        )

    # Instantiate the agent with empty configuration (uses defaults)
    agent: object = agent_cls(config={})

    # Execute the task and return the result
    return agent.run(task=task)
    # Alternative invocation with file paths and execution tracking:
    # return agent.run(task=task, work_dir=work_dir, execution_id=execution_id)


if __name__ == "__main__":
    """
    Command-line entry point for executing coding tasks.

    When this module is run as a script, it processes predefined tasks using the
    configured agents. This is useful for testing, debugging, and batch execution.
    """
    # Example task: Generate FastAPI CRUD endpoints
    # input_state = "Write a detailed FastAPI endpoint for CRUD ops for a llm application that can take user input in text of file format"

    # Store manager inventory workflow task specification (business requirements)
    input_state: str = """As a store manager, I want to add a new product to the inventory so that I can track its availability and manage its stock levels.
As a store manager, I want to remove a product from the inventory so that I can discontinue its sale and update its availability status.
As a store manager, I want to edit the details of an existing product in the inventory so that I can update its information or correct any errors.
"""

    # Execute the task with the default Python agent
    run(task=input_state)

    # Alternative execution with explicit output directory and execution tracking:
    # run(task="Write fibonacci series", work_dir="output/1", language="python")