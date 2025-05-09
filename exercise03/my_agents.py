import os
from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List
from agents import Agent, RunContextWrapper, Runner, TResponseInputItem
from agents.extensions.models.litellm_model import LitellmModel
from pydantic import BaseModel
from .my_tools import MCPServerRepository, get_connections, think, ask_for_clarification, get_calendar_appointments


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
    model=LitellmModel(model=os.getenv("AGENT_MODEL"), api_key=os.getenv("OPENROUTER_API_KEY")),
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
    model=LitellmModel(model=os.getenv("AGENT_MODEL"), api_key=os.getenv("OPENROUTER_API_KEY")),
)


class OpenStreetMapAgent(Agent):
    @classmethod
    async def setup(cls):
        """
        TODO:
            1. Obtain the global `MCPServerRepository` singleton.
            2. Retrieve the server named **"openstreetmap"**.
            3. Instantiate **OpenStreetMapAgent** with:
                • A clear instruction string.
                • `tools` list containing at least `think` and `ask_for_clarification`.
                • `mcp_servers=[the_openstreetmap_server]`.
                • A `LitellmModel` instance (same env vars as above).

        Hints:
            • `MCPServerRepository.get_instance()` is an async classmethod.
            • The agent constructor is `Agent.__init__(name, instructions, tools, mcp_servers, model)`.
            • Keep the method `@classmethod` and return `cls(...)`.
        """
        # === Your code here ================================================= #
        pass
        # ==================================================================== #


triage_agent_system_prompt = """
You are a smart assistant that helps users plan their trips based on public transport
schedules, their calendar appointments, and other relevant information. You can make use
of geographical location data such as nearby places, route directions, etc.

1. First find the connections for the given start and end locations, date and time.
2. Then, check the user's calendar appointments for the travel date.
3. If appropriate, take into account contextual information to improve the trip planning.

When referring to an appointment, always mention the name of the appointment.
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
        # TODO:
        #   After you finish OpenStreetMapAgent.setup(), add it below like so:
        #
        #   asyncio.run(OpenStreetMapAgent.setup()).as_tool(
        #       tool_name="...",
        #       tool_description="...",
        #   ),
    ],
    model=LitellmModel(model=os.getenv("AGENT_MODEL"), api_key=os.getenv("OPENROUTER_API_KEY")),
)


async def execute_agent(user_input: str, history: List[Dict[str, str]]) -> tuple[Any, list[TResponseInputItem]]:
    """
    Executes the main agent with the given input and returns the response and the updated history.

    Args:
        user_input: The user's message
        history: The conversation history

    Returns:
        A tuple containing (response_message, updated_history)
        If the guardrail was triggered, updated_history will be None indicating
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
