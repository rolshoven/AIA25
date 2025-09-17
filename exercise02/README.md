# Exercise 2 · Build a Multi‑Agent Transport Scheduler 🚍🤖

Welcome back, Agent‑builders!
 In this lab you’ll **combine three tiny AIs into one helpful travel‑planning system** that checks your calendar and picks the best public‑transport route.
 Along the way you’ll get a taste of real‑world **multi‑agent systems (MAS)** design: agents that *cooperate*, *specialise*, and *delegate*.

------

## ✨ Learning goals

By the end you can

1. explain why we compose agents instead of making one giant prompt,
2. wire up agents with `Agent.as_tool()` to call each other, and
3. give a user human‑level answers sourced from live APIs *and* personal context.

------

## 📚 Background — What is a Multi‑Agent System?

A **multi‑agent system (MAS)** is a network of autonomous programs (agents) that interact to solve problems no single agent could handle elegantly.
 Each agent has limited knowledge, but *together* they exhibit emergent intelligence—think swarm robotics, algorithmic trading teams, or (like here) itinerary planners.
 In the OpenAI Agents Python framework each `Agent` gets:

- a **system prompt** (rules & persona),
- a set of **tools** (function calls), and
- a **language model**.
  When you wrap an agent as a tool, you turn its entire reasoning loop into a single callable step for another agent.



------

## 🚶‍♂️ Step 1: Scan the starter code

Open **`exercise02/my_agents.py`**.
 You’ll see two `# TODO:` sections for `scheduling_agent` and `triage_agent`.

------

## 🚄 Step 2: Build the Scheduling Agent

*Goal*: choose the *earliest* route that still lands ≥ **15 min before** the next calendar item.

```python
# Your implementation here
scheduling_agent = Agent(
    name='Scheduling Agent',
    instructions=# Add appropriate system instructions,
    tools=# Include necessary tools for scheduling,
)
```

**What happens here?**

1. Your scheduling agent needs a system prompt that prioritizes timeliness.
2. Consider what tools would help with scheduling decisions:
   - Something for internal reasoning
   - Something for handling unclear user requests
   - Something to access calendar information
3. Choose an appropriate model configuration.

> 🔗 Docs: [Agent Models](https://openai.github.io/openai-agents-python/models/)

------

## 🤝 Step 3: Turn agents into tools

```python
# Transform your agents into callable tools
public_transport_agent.as_tool(
    tool_name=...,
    tool_description=...,
)
```

*Why?* When you wrap an agent as a tool, you expose its capabilities through a clean function interface, hiding internal complexity.

------

## 🧑‍⚖️ Step 4: Build the Triage (Orchestrator) Agent

```python
from .prompts import triage_agent_system_prompt
from openai_agents import Agent

triage_agent = Agent(
    name='Triage Agent',
    instructions=...,
    tools=[...]
)
```

**Execution flow**

1. Triager receives the user’s natural‑language question.
2. It calls `find_transport_routes` to get *candidates*.
3. Passes those candidates to `select_best_connection` (scheduling agent).
4. Returns a friendly, single best option to the user.

------

## 🛣️ Where next?

- Play around with the prompt, can you make it better?
- What happens if you remove some tools, or switch them up?
- You could add some more appointments using the `calendar_client.py`

Happy hacking — may your agents arrive *fashionably early*! 🚉