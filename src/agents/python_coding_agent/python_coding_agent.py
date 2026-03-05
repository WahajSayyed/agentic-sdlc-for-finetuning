from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from .prompt.python_coding_agent_prompt import Python_Coding_Prompt
from typing import Dict
from typing_extensions import TypedDict
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(
    project_name="agentic_sdlc",
    output_dir="/home/wahaj/study/product_WJ/emissions",
    log_level="info"
)

llm = ChatOpenAI(
    base_url= "http://localhost:8080/v1",
    model="Qwen2.5-7B-Instruct.Q4_0.gguf",
    api_key="not_needed",
    # callbacks=[SimpleLogger()]
)

class OverAllState(TypedDict):
    task: str
    output: str #Dict[str, str]

def coding_assistance(state: OverAllState):
    task = state["task"]
    prompt = Python_Coding_Prompt(task)
    messages = [SystemMessage(content=prompt.python_coding_agent_prompt)]
    response = llm.invoke(messages)

    return {"output": response.content}

build = StateGraph(OverAllState)
build.add_node("assisstant", coding_assistance)

build.add_edge(START, "assisstant")
build.add_edge("assisstant", END)

graph = build.compile()

# input_message = HumanMessage(content="Write a hello world program")
tracker.start()
result = graph.invoke({"task": "Write a hello world program"})
print(result)

tracker.stop()
