import asyncio
from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List

from agents import Agent, RunContextWrapper, Runner, TResponseInputItem
from pydantic import BaseModel

from .my_tools import (
    MCPServerRepository,
    ask_for_clarification,
    get_calendar_appointments,
    get_connections,
    think,
)


class GlobalContext(BaseModel):
    """
    This class holds the global context for the agent, including the current date and time.
    It is used to provide context to the agent during its execution.
    """

    current_date: str = ""  # Date in YYYY-MM-DD format
    current_time: str = ""  # Time in HH:MM:SS format


def scheduling_agent_system_prompt(context: RunContextWrapper[GlobalContext], agent: Agent[GlobalContext]) -> str:
    ctx = context.context
    return dedent(
        f"""
        You are a scheduling assistant that optimizes transport recommendations based on calendar appointments.

        Current date: {ctx.current_date}
        Current time: {ctx.current_time}

        # Tasks
        - Evaluate transport options against calendar appointments
        - Recommend optimal connections with rationale
        - Ensure journey-appointment alignment

        # Process
        1. For travel requests: Use YYYY-MM-DD format. Retrieve calendar appointments for specified date.
        2. Analyze connections for: appointment conflicts, 15+ min buffers, journey duration, transfers, reliability.
        3. Recommend with: connection details, selection rationale, and schedule considerations.
        4. If no appointments exist, select the most efficient connection.
        """
    )


scheduling_agent = Agent(
    name="Scheduling Agent",
    instructions=scheduling_agent_system_prompt,
    tools=[think, ask_for_clarification, get_calendar_appointments],
)


def public_transport_agent_system_prompt(
    context: RunContextWrapper[GlobalContext], agent: Agent[GlobalContext]
) -> str:
    ctx = context.context
    return dedent(
        f"""You are a public transport assistant that helps users find the best public transport
        connections based on their needs. Whenever you receive a query, you first think about it
        and figure out what the user is asking for. Then you either directly answer the question
        if you know the answer, or you make a plan in which order you will call the tools to get
        the required information. If there is no combination of tool calls that can help you
        answer the questions, you should ask the user for more information. If you are unsure about
        the start or end location or about the specific travel date and time that you should use in
        the tool calls, you should ask the user for clarification.

        Current date: {ctx.current_date}
        Current time: {ctx.current_time}

        You have access to the following tools:
        - think: Use this tool for planning and observing the current state of the conversation.
        - get_connections: Find the best public transport connections between two locations.
        - ask_for_clarification: Ask the user for more information if needed.

        If you leave the date and time empty, the current date and time will be used.

        Never call a tool twice with the same parameters. Always inspect the tool output and
        ask yourself whether that already answers the user's question. If it does, stop calling tools and
        synthesize the information into a clear response. Provide a final answer to the user's query.

        Whenever you plan something, immediately follow up with the plan before answering the question.
        """
    )


public_transport_agent = Agent(
    name="Public Transport Agent",
    instructions=public_transport_agent_system_prompt,
    tools=[think, ask_for_clarification, get_connections],
)


class OpenStreetMapAgent(Agent):
    @classmethod
    async def setup(cls):
        mcp_repo = await MCPServerRepository.get_instance()

        return cls(
            name="OpenStreetMap Agent",
            instructions=(
                "You are an expert at providing location-based information. Use the available tools "
                "to answer questions about route directions, nearby places, points of interest, etc."
            ),
            tools=[think, ask_for_clarification],
            mcp_servers=[mcp_repo.get_server("openstreetmap")],
        )


triage_agent_system_prompt = """
You are a smart assistant that helps users plan their trips based on public transport
schedules, their calendar appointments, and other relevant information. You can make use
of geographical location data such as nearby places, route directions, etc.

1. First find the connections for the given start and end locations, date and time.
2. Then, check the user's calendar appointments for the travel date.
3. If appropriate, take into account contextual information to improve the trip planning.

When referring to an appointment, always mention the name of the appointment. Do not recall
points of interests (such as nearby places) or other geographical information on your own, 
ALWAYS use the explore_locations tool to ensure up-to-date information. You do not have access
to any other location services.

Answer in a friendly and helpful manner.
"""

triage_agent = Agent(
    name="Triage agent",
    instructions=triage_agent_system_prompt,
    tools=[
        think,
        ask_for_clarification,
        public_transport_agent.as_tool(
            tool_name="find_transport_routes",
            tool_description="Find public transport routes between two locations for a specific date and time",
        ),
        scheduling_agent.as_tool(
            tool_name="select_best_connection",
            tool_description=(
                "Select the optimal transport connection by first getting the user's appointments and "
                "then determine the connection that best fits with the user's calendar appointments"
            ),
        ),
        asyncio.run(OpenStreetMapAgent.setup()).as_tool(
            tool_name="explore_locations",
            tool_description=(
                "Find information about locations. Can be used to geocode addresses, find nearby places, "
                "get walking directions from point A to B, and suggest meeting spots for two people in "
                "different locations."
            ),
        ),
    ],
)


async def execute_agent(user_input: str, history: List[Dict[str, str]]) -> tuple[Any, list[TResponseInputItem]]:
    """
    Executes the main agent with the given input and returns the response and the updated history.

    Args:
        user_input: The user's message
        history: The conversation history

    Returns:
        A tuple containing (response_message, updated_history)
        the history should not be updated
    """
    current_history = history + [{"role": "user", "content": user_input}]

    current_datetime = datetime.now()
    date_only = current_datetime.strftime("%Y-%m-%d")
    time_only = current_datetime.strftime("%H:%M:%S")

    result = await Runner.run(
        starting_agent=triage_agent,
        input=current_history,
        context=GlobalContext(current_date=date_only, current_time=time_only),
    )

    return result.final_output, result.to_input_list()
