from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import re
import os

load_dotenv()


class PlannerState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], "Conversation messages"]
    goal: str
    tasks: List[dict]
    plan: str



llm = ChatGroq(
    temperature=0.2,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)



goal_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI Goal Analyzer. Extract key deliverables, outcomes, and milestones concisely."),
    ("human", "Goal: {goal}")
])

task_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Task Generator AI.
    Break the goal into clear, actionable tasks with short descriptions and expected outcomes.
    Keep tasks within the duration implied in the goal."""),
    ("human", "Goal: {goal}")
])

dependency_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Dependency Manager AI.
    Assign logical dependencies between tasks.
    Respond in JSON format like:
    [{{"id": "T1", "task": "Research market", "depends_on": []}}, ...]"""),
    ("human", "Tasks: {tasks}")
])

timeline_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Timeline Planner AI.
    The goal duration is {duration_weeks} weeks.
    Distribute all tasks realistically within this timeframe.
    Output JSON like:
    [{{"id": "T1", "task": "...", "depends_on": [], "start_week": 1, "end_week": 1}}, ...]"""),
    ("human", "Tasks: {tasks}")
])



def extract_duration(goal: str) -> int:
    """
    Extract duration in weeks from the goal text.
    """
    goal = goal.lower()
    match = re.search(r'(\d+)\s*(month|week)', goal)
    if not match:
        return 8 

    value = int(match.group(1))
    unit = match.group(2)

    if "month" in unit:
        return value * 4
    elif "week" in unit:
        return value
    return 8



def analyze_goal(state: PlannerState):
    response = llm.invoke(goal_prompt.format_messages(goal=state["goal"]))
    state["messages"].append(AIMessage(content=response.content))
    return state


def generate_tasks(state: PlannerState):
    response = llm.invoke(task_prompt.format_messages(goal=state["goal"]))
    state["messages"].append(AIMessage(content=response.content))

    
    lines = [t.strip("-•1234567890. ").strip() for t in response.content.split("\n") if t.strip()]
    state["tasks"] = [{"id": f"T{i+1}", "task": line, "depends_on": []} for i, line in enumerate(lines)]

    return state


def manage_dependencies(state: PlannerState):
    response = llm.invoke(dependency_prompt.format_messages(tasks=state["tasks"]))
    state["messages"].append(AIMessage(content=response.content))

   
    import json
    try:
        deps = json.loads(response.content)
        
        id_map = {old["id"]: f"T{i+1}" for i, old in enumerate(deps)}
        for i, task in enumerate(deps):
            task["id"] = id_map[task["id"]]
            task["depends_on"] = [id_map.get(d, d) for d in task.get("depends_on", [])]
        state["tasks"] = deps
    except Exception:
        
        pass

    return state


def plan_timeline(state: PlannerState):
    duration_weeks = extract_duration(state["goal"])
    response = llm.invoke(timeline_prompt.format_messages(tasks=state["tasks"], duration_weeks=duration_weeks))
    state["messages"].append(AIMessage(content=response.content))
    state["plan"] = response.content
    return state



def create_task_plan(goal: str):
    state: PlannerState = {
        "messages": [],
        "goal": goal,
        "tasks": [],
        "plan": ""
    }

    state = analyze_goal(state)
    state = generate_tasks(state)
    state = manage_dependencies(state)
    state = plan_timeline(state)

    return state["plan"]
