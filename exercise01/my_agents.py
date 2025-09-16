from textwrap import dedent
from typing import Any, Dict, List

from agents import Agent, Runner, TResponseInputItem

from .my_tools import (
    ask_for_clarification,
    get_connections,
    get_current_date_and_time,
    think,
)

public_transport_agent = Agent(
    name="Public Transport Agent",
    instructions=dedent(
        """You are a public transport assistant that helps users find the best public transport
        connections based on their needs. Whenever you receive a query, you first think about it
        and figure out what the user is asking for. Then you either directly answer the question
        if you know the answer, or you make a plan in which order you will call the tools to get
        the required information. If there is no combination of tool calls that can help you
        answer the questions, you should ask the user for more information. If you are unsure about
        the start or end location or about the specific travel date and time that you should use in
        the tool calls, you should ask the user for clarification.

        You have access to the following tools:
        - think: Use this tool for planning and observing the current state of the conversation.
        - get_connections: Find the best public transport connections between two locations.
        - get_current_date_and_time: Get the current date and time in ISO format.
        - ask_for_clarification: Ask the user for more information if needed.

        If you leave the date and time empty, the current date and time will be used.

        Never call a tool twice with the same parameters. Always inspect the tool output and
        ask yourself whether that already answers the user's question. If it does, stop calling tools and
        synthesize the information into a clear response. Provide a final answer to the user's query.

        Whenever you plan something, immediately follow up with the plan before answering the question.
        """
    ),
    tools=[think, ask_for_clarification, get_connections, get_current_date_and_time],
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

    result = await Runner.run(starting_agent=public_transport_agent, input=current_history)

    return result.final_output, result.to_input_list()
