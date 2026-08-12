import uuid
import json
from typing import AsyncGenerator, TypedDict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from app.config import get_settings
from app.models.ai import AIUsageLog

settings = get_settings()

class AgentState(TypedDict):
    messages: list[BaseMessage]
    context: str

class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Use ChatOpenAI class to talk to hosted Ollama (or OpenAI) since it supports base_url and api_key natively.
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                streaming=True
            )
        else:
            base_url = settings.OLLAMA_BASE_URL
            if base_url and not base_url.endswith("/v1"):
                base_url = f"{base_url}/v1"
            
            self.llm = ChatOpenAI(
                model="llama3", # Default model, can be overridden if needed
                base_url=base_url if base_url else None,
                api_key=settings.OLLAMA_API_KEY or "ollama",
                streaming=True
            )

    async def _log_usage(self, user_id: uuid.UUID, endpoint: str, project_id: uuid.UUID | None = None):
        log = AIUsageLog(
            user_id=user_id,
            project_id=project_id,
            endpoint=endpoint,
            prompt_tokens=0,
            completion_tokens=0,
            cost=0.0
        )
        self.db.add(log)
        await self.db.commit()

    async def analyze_task(self, user_id: uuid.UUID, task_id: uuid.UUID, focus: str | None) -> AsyncGenerator[str, None]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert project manager AI. Analyze the following task. Focus on: {focus}."),
            ("human", "Task ID: {task_id}")
        ])
        chain = prompt | self.llm
        
        await self._log_usage(user_id, "/ai/tasks/analyze")

        async for chunk in chain.astream({"task_id": str(task_id), "focus": focus or "general analysis"}):
            yield chunk.content

    async def suggest_subtasks(self, user_id: uuid.UUID, task_id: uuid.UUID) -> list[str]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Suggest 3-5 logical subtasks for the given task. Return ONLY a JSON array of strings."),
            ("human", "Task ID: {task_id}")
        ])
        chain = prompt | self.llm
        
        await self._log_usage(user_id, "/ai/tasks/suggest-subtasks")
        
        response = await chain.ainvoke({"task_id": str(task_id)})
        try:
            content = response.content.replace("```json", "").replace("```", "").strip()
            subtasks = json.loads(content)
            if isinstance(subtasks, list):
                return subtasks
            return ["Invalid format returned by AI"]
        except json.JSONDecodeError:
            return ["Failed to parse AI suggestions"]

    async def summarize_project(self, user_id: uuid.UUID, project_id: uuid.UUID) -> AsyncGenerator[str, None]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the current status of the project based on the context. Highlight any blockers."),
            ("human", "Project ID: {project_id}")
        ])
        chain = prompt | self.llm
        
        await self._log_usage(user_id, "/ai/projects/summarize", project_id=project_id)
        
        async for chunk in chain.astream({"project_id": str(project_id)}):
            yield chunk.content

    async def chat(self, user_id: uuid.UUID, message: str, project_id: uuid.UUID | None) -> AsyncGenerator[str, None]:
        async def call_model(state: AgentState):
            messages = state["messages"]
            system_msg = SystemMessage(content=f"You are a helpful AI assistant for DevFlow. Context: {state['context']}")
            response = await self.llm.ainvoke([system_msg] + messages)
            return {"messages": [response]}
        
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.set_entry_point("agent")
        workflow.add_edge("agent", END)
        app = workflow.compile()

        await self._log_usage(user_id, "/ai/chat", project_id=project_id)

        context_str = f"Project ID: {project_id}" if project_id else "General workspace"
        inputs = {"messages": [HumanMessage(content=message)], "context": context_str}

        async for event in app.astream_events(inputs, version="v2"):
            if event["event"] == "on_chat_model_stream":
                yield event["data"]["chunk"].content
