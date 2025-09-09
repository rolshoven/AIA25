# Exercise 1 · Meet Your First Agent 🚍

Welcome to the workshop!  
In this first exercise, you’ll **set up your environment and run your very first transport-planning agent**.  
Think of this step as the “hello world” of multi-agent systems: you don’t need to change anything (unless you’re curious).

------

## ✨ Learning goals

By the end you can

1. start the workshop app and select your agent,  
2. run the **Public Transport Agent** and see how it uses tools, and  
3. inspect execution traces in **MLflow**.

------

## 📚 Background — The Public Transport Agent

Your starter agent already knows how to:

- **think** (plan steps and reflect),
- **get connections** (fetch transport routes from the Swiss public-transport API),
- **get the current date & time**, and
- **ask for clarification** if something is missing.

The agent follows a simple loop:  
plan → call tools → synthesize → answer the user.  
All of this logic lives in [`my_agents.py`](./my_agents.py) and [`my_tools.py`](./my_tools.py).

------

## 🚶 Step 1: Run the App

From the project root, launch the Chainlit interface:

```bash
uv run chainlit run aia25/app.py -w -h
```

Then open the browser window that pops up.

------

## 🚄 Step 2: Select Your Agent

1. Click the ⚙️ gear icon in the chat sidebar.  
2. Choose **exercise01 → execute_agent** from the agent dropdown.  
3. Type a request like:

   ```
   Find me a train from Bern to Zurich at 9am tomorrow
   ```

Watch as the agent plans, calls tools, and replies with a connection.

------

## 🔍 Step 3: Inspect the Trace

Each conversation run is logged to **MLflow**. Start the dashboard:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Then visit [http://localhost:5000/](http://localhost:5000/) to see how your agent executed the steps.

If that does not work, try out a different port. You will have to change it on line 20 in `aia25/bootstrap.py` as well:

```python
mlflow.set_tracking_uri("http://localhost:5000")
```

------

## 🛣️ Where next?

- Try asking for different routes, dates, or vague queries (“I need to get to Geneva this afternoon”).  
- Notice how the agent asks for clarification if key info is missing.  
- Curious? Peek into [`my_tools.py`](./my_tools.py) and see how API calls are wrapped as tools.

Happy travels — you’ve just launched your first AI agent! 🚉
