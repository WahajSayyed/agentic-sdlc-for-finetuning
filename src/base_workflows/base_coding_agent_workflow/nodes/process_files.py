from src.base_workflows.base_coding_agent_workflow.state import BaseAgentState, BaseFileAgentState
from src.config.logging_config import logger

def make_process_files_node(file_subgraph):
    """Factory that injects the compiled subgraph into the nodes"""
    
    def process_files_node(state: BaseAgentState):
        """Process each file sequentially through the subgraph."""
        logger.info(f"Processing {len(state['plan']['files'])} files sequentially")
        
        all_code_changes = []
        all_written_files = []

        for file_plan in state["plan"]["files"]:
            logger.info(f"Processing file: {file_plan['path']}")
            
            # Build per-file initial state
            file_state = BaseFileAgentState(
                execution_id=state["execution_id"],
                work_dir=state["work_dir"],
                task=state["task"],
                feedback=state.get("feedback"),
                retry_count={},
                file_plan=file_plan,
                existing_file_content=(
                    (state.get("existing_files") or {}).get(file_plan["path"])
                    if file_plan["action"] == "update"
                    else None
                ),
                code_change=None,
                review=None,
                written_files=[],
                static_check_success=None,
                static_check_output=None,
            )

            # Run subgraph for this file
            result = file_subgraph.invoke(file_state)

            # Collect results
            if result.get("code_change"):
                all_code_changes.append(result["code_change"])
            final_written = list(set(result.get("written_files", [])))
            if final_written:
                all_written_files.extend(final_written)

            logger.info(f"Finished processing: {file_plan['path']}")

        return {
            **state,
            "code_changes": all_code_changes,
            "written_files": all_written_files,
        }
    return process_files_node