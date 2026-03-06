
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(
    base_url="http://localhost:8080/v1",
    # model="Qwen2.5-7B-Instruct.Q4_0.gguf",
    model="Qwen2.5-Coder-7B-Instruct.Q4_0.gguf",
    api_key="not_needed",
    # callbacks=[SimpleLogger()]
)