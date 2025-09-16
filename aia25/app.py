from bootstrap import *  # noqa: F403,E402

import importlib
import logging
from types import ModuleType

import mlflow
import chainlit as cl
from agents import enable_verbose_stdout_logging

logger = logging.getLogger("chainlit")


EXERCISE_TO_MODULE_IMPORT = {
    "Exercise 1": "exercise01.my_agents",
    "Exercise 2": "exercise02.my_agents",
    "Exercise 3": "exercise03.my_agents",
    "Exercise 4": "exercise04.my_agents",
    "Exercise 2 Solution": "solution_exercise02.my_agents",
    "Exercise 3 Solution": "solution_exercise03.my_agents",
    "Exercise 4 Solution": "solution_exercise04.my_agents",
}


def load_exercise_agents_module(exercise_name: str) -> ModuleType:
    """
    Loads the agents module for the given exercise name.

    Args:
        exercise_name: The name of the exercise to load.

    Returns:
        The loaded agents module.
    """
    module_name = EXERCISE_TO_MODULE_IMPORT[exercise_name]

    if module_name:
        if mlflow_tracing_enabled():
            mlflow.set_experiment(exercise_name)
            logger.info(f"MLFlow experiment set to {exercise_name}")

        return importlib.import_module(module_name)

    raise ImportError(f"Module for {exercise_name} not found")


def mlflow_tracing_enabled() -> bool:
    """
    Check if MLFlow tracing is enabled.

    Returns:
        True if MLFlow tracing is enabled, False otherwise.
    """
    return bool(os.getenv("MLFLOW_TRACING_ENABLED", "False"))


async def get_agent_response(user_message: str) -> str:
    """
    Run the agent with the chat history and the given user message and update the history.
    Returns only the final output.

    Args:
        user_message: The user's message.

    Returns:
        The agent's response.
    """
    # Retrieve the history from the user session and add the user message to it
    history = cl.user_session.get("history") or []

    # Retrieve the exercise's agents module from the user session
    exercise = cl.user_session.get("exercise")

    # Execute agent with input and handle exceptions in the service layer
    response, updated_history = await exercise.execute_agent(user_input=user_message, history=history)

    # Only update history if we got a valid updated history back
    if updated_history is not None:
        cl.user_session.set("history", updated_history)

    return response


@cl.on_chat_start
async def on_chat_start():
    settings = await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="exercise",
                label="Exercise",
                values=[
                    "Exercise 1",
                    "Exercise 2",
                    "Exercise 3",
                    "Exercise 4",
                    "Exercise 2 Solution",
                    "Exercise 3 Solution",
                    "Exercise 4 Solution",
                ],
                initial_index=0,
            ),
            cl.input_widget.Switch(
                id="verbose_stdout_logging",
                label="Enable verbose stdout logging",
                initial_value=False,
                description="Enable verbose logging for stdout. This is useful for debugging.",
            ),
        ]
    ).send()

    # Update the agent execution function based on the selected exercise
    await on_settings_update(settings)

    # Reset the chat history
    cl.user_session.set("history", [])


@cl.on_settings_update
async def on_settings_update(settings):
    # Update the agent execution function based on the selected exercise
    cl.user_session.set("exercise_name", settings["exercise"])
    cl.user_session.set("exercise", load_exercise_agents_module(settings["exercise"]))

    # If user selected verbose logging, enable it (can't be disabled until restart)
    if settings["verbose_stdout_logging"]:
        enable_verbose_stdout_logging()


@cl.on_message  # this function will be called every time a user inputs a message in the UI
async def handle_message(message: cl.Message):
    response = await get_agent_response(message.content)
    author = cl.user_session.get("exercise_name")
    await cl.Message(content=response, author=author).send()


@cl.server.app.on_event("shutdown")
async def on_shutdown():
    # Get the current selected exercise from the user session
    current_exercise = cl.user_session.get("exercise", None)

    if current_exercise and hasattr(current_exercise, "MCPServerRepository"):
        repo = await current_exercise.MCPServerRepository.get_instance()
        await repo.aclose()
