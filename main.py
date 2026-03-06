from src.agents.python_coding_agent.agent import PythonCodingAgent
# from src.agents.javascript_agent.agent import JavaScriptCodingAgent

AGENTS = {
    "python": PythonCodingAgent,
    # "javascript": JavaScriptCodingAgent,
}

# def run(task: str, work_dir: str, language: str = "python", execution_id: int = 4):
def run(task: str, language: str = "python"):    
    agent_cls = AGENTS.get(language)
    if not agent_cls:
        raise ValueError(f"Unsupported language: {language}. Choose from {list(AGENTS.keys())}")

    agent = agent_cls(config={})
    return agent.run(task=task)
    # return agent.run(task=task, work_dir=work_dir, execution_id=execution_id)

if __name__ == "__main__":
    run(task="Write fibonacci series")
    # run(task="Write fibonacci series", work_dir="output/1", language="python")