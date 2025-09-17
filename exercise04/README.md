# Exercise 4 · Guardrail‑Powered Trip Planner 🚦🗺️

Welcome back, intrepid Agent‑smiths!
 In this lab you’ll **add topic‑aware guardrails to a multi‑agent trip‑planning system** so that irrelevant or malicious queries are filtered *before* they reach your heavy‑duty agents.
 Along the way you’ll touch every layer of a real‑world **safety‑centric MAS (multi‑agent system)**: purpose‑built guardrail agents, validation functions, and graceful fall‑backs.

------

## ✨ Learning goals

By the end you can

1. explain why we wrap a *tiny* guardrail agent around bigger reasoning agents,
2. implement an `input_guardrail` that blocks or routes user messages, and
3. propagate guardrail signals cleanly through an async agent runner.

------

## 🛡️ Background — What is a Guardrail Agent?

**A guardrail agent** is a *specialised* AI whose sole job is to decide whether an incoming message should be processed further.
 Instead of letting your main agents waste tokens (or do something dangerous!) you:

1. hand the message to the guardrail,
2. parse a structured JSON verdict, and
3. act accordingly (continue, ask for clarification, or refuse).

In our Python framework this pattern is baked in via `@input_guardrail` decorators and a simple `GuardrailFunctionOutput` return type.

Have a look at official documentation on [Input Guardrails](https://openai.github.io/openai-agents-python/guardrails/)

------

## 🚶‍♂️ Step 1: Scan the starter code

Open **`exercise04/my_agents.py`** (listing below).
 You’ll notice four `# TODO:` tags:

There are 5 TODOS in total. Most of the things you have to implement are already set up for you.  
To get a better understanding of what to do, you can have a look at the documenation links we provided in this readme.  
If you still feel lost, you can always have a look at the solution.

Take a moment to skim the surrounding context so each TODO makes sense.

------

## 🛑 Step 2: Build the Topic‑Check Guardrail Agent

*Goal*: return a **boolean verdict** (`is_relevant`) and short reasoning for *every* user message.

```python
class TopicCheckOutput(BaseModel):
    is_relevant: bool
    reasoning: str

guardrail_agent = Agent(
    name="Topic Check Guardrail",
    instructions=...,  # ✅ use the prompt already provided above
    output_type=...,   # ✅ your structured schema
)
```

**Tips**

1. The system prompt (`guardrail_agent_system_prompt`) is ready—just wire it in.
2. Use the `TopicCheckOutput` model, this tells the agent what JSON structure to return, and allows you to handle the outputs in a typed way.
3. Keep the model *the same as before*.

> 🔗 Docs: This is OpenAI's description of what structured outputs are [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat)

------

## 🔍 Step 3: Implement the `topic_guardrail` Function

Decorated with `@input_guardrail`, this async function is called **before** the main conversation flow.

Key tasks:

1. Send the **raw user text** to `guardrail_agent`.
2. Parse the agent’s JSON into `TopicCheckOutput`.
3. Return `GuardrailFunctionOutput(allowed=..., message=...)` where:
   - `allowed` is `output.is_relevant`.
   - `message` politely explains *why* a request was blocked (only when disallowed).

```python
@input_guardrail
async def topic_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:

    result = ... # Run the guardrail agent

    return GuardrailFunctionOutput(
        output_info=result.reasoning,
        tripwire_triggered=not result.is_relevant,
    )
```

Feel free to tweak the block message style.

------

## 🤝 Step 4: Catch Guardrail Exceptions Gracefully

Inside `execute_agent` we already wrap the call to `Runner.run(...)` in a `try`/`except`—you just need to **capture the specific exception** (see [Input Guardrails](https://openai.github.io/openai-agents-python/guardrails/) again) raised when a guardrail blocks input (check the framework’s docs or explore with a quick REPL).

```python
try:
    result = await Runner.run(
        starting_agent=triage_agent,
        input=current_history,
        context=GlobalContext(current_date=date_only, current_time=time_only),
    )

    return result.final_output, result.to_input_list()
except ... # Handle the specific exception
```

Returning `None` for history tells the caller *not* to store that turn.

------

## 🚦 Step 5: Test the Flow

1. Run `uv run app` (or the VsCode debugger).
2. Try questions *inside* scope, e.g. “Find me a train from Zurich to Bern tomorrow at 8 am.”
3. Try questions *outside* scope, e.g. “Who won the 2025 Eurovision?”
4. Observe how irrelevant queries are politely refused *before* any expensive tool calls.

------

## 🛣️ Where next?

- **Add more topics**: extend the guardrail schema so your assistant covers hotels, flights, or weather.
- **Adapt the prompt**: Try to make it more/less restrictive. Can it also filter for arrogant comments?

Happy hacking — and may your agents stay *on track* and *on topic*! 🚂📅