from langchain_core.prompts import ChatPromptTemplate

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior software architect.

Your job is to create a precise implementation plan.

Rules:
- Prefer updating existing files over creating new ones.
- Only create new files if necessary.
- Respect the apparent project structure.
- Keep modifications minimal and modular.
- Return structured JSON only.
"""),
    ("user", """
Task:
{task}

Working Directory:
{work_dir}

Repository file structure:
{file_structure}

{format_instructions}
""")
])