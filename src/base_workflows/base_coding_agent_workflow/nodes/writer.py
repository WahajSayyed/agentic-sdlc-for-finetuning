import os
import shutil
from src.base_workflows.base_coding_agent_workflow.state import BaseFileAgentState
from src.config.logging_config import logger

def writer_node(state: BaseFileAgentState, backup: bool = True):
    """
    Persist code changes to disk safely.

    Args:
        state: AgentState containing code_changes
        backup: wheather to backup overwritten files
    """
    logger.info("Executing Writer Node")
    written_files = []

    code_change = state.get("code_change")
    if not code_change:
        logger.warning("No code_change found in the state, skipping writer.")
        return {**state, "written_files": [], "code_changes": []}
    
    work_dir = state["work_dir"]
    path = code_change["path"]
    content = code_change["content"]
    action = code_change["action"]    
    if not path.startswith(work_dir):
        if path[0] == "/" :
            logger.critical(f"skipping the file due to wrong file path: {path}")
            return {**state, "written_files": [], "code_changes": []}
        path = os.path.join(work_dir, path)
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if backup and action == "update" and os.path.exists(path):
        backup_path = path + ".bak"
        shutil.copyfile(path, backup_path)
        logger.debug(f"Backup created: {backup_path}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    written_files.append(path)

    # state["written_files"] = written_files
    logger.debug(f"Written Files: \n{written_files}")
    return {
        **state,
        "written_files": [path],
        "code_changes": [code_change] 
    }
