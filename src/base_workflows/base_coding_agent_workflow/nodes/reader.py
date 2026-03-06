from src.base_workflows.base_coding_agent_workflow.state import BaseAgentState
from src.config.logging_config import logger
from src.tools.read_file import read_file

def reader_node(state: BaseAgentState):
    logger.info("Executing Reader Node")
    plan = state["plan"]
    files_to_update = [
        file["path"] for file in plan["files"]  # ignore type-check
        if file["action"] == "update"
    ]
    existing_files = {}

    for path in files_to_update:
        content = read_file.invoke(path)
        existing_files[path] = content

    state["existing_files"] = existing_files
    logger.debug(f"Existing Files: \n{existing_files}")
    return state