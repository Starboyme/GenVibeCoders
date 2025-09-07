# Tripmate AI Server

This server orchestrates a multi-agent travel concierge system using the ADK framework (`adk create_server`). Each agent is designed to handle a specific aspect of trip planning, from user preferences to itinerary generation and dynamic adjustments.

## Folder Structure

- `tripmate/`
  - `agent.py` — Main entry point for the root orchestrator agent.
  - `prompt.py` — Initial prompt/instructions for the root agent.
  - `.env` — Environment variables for cloud and AI configuration.
  - `library/` — Shared functions/utilities for use across agents.
  - `tools/` — Custom tools for agent actions.
  - `sub_agents/`
    - Each subfolder (e.g., `budgetOptimization/`, `userPreference/`, etc.) contains:
      - `agent.py` — Main file for the specialized agent.
      - `prompt.py` — Initial prompt for the agent.

## Getting Started

### 1. Install Dependencies

Make sure you have Python 3.9+ and install required packages:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `tripmate/.env` with your Google Cloud project details and region.

**Authentication Steps:**
- Obtain a Google Cloud service account JSON key file.
- Set the environment variable before running or testing:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
  ```
- Ensure your service account has access to Vertex AI and any other required GCP services.

### 3. Running and Testing Agents

#### Run the Server (CLI)

```bash
adk run_server tripmate
```

#### Run the Server (Web Interface)

```bash
adk web tripmate
```
- Opens a web UI at `http://localhost:8000` for interactive agent testing.

#### Test Individual Agents (CLI)

```bash
adk agent_cli tripmate/sub_agents/budgetOptimization/agent.py
adk agent_cli tripmate/sub_agents/userPreference/agent.py
# ...repeat for other agents as needed
```

#### Build/Scaffold New Agents

```bash
adk create_agent tripmate/sub_agents/newAgent
```
- This scaffolds a new agent folder with `agent.py` and `prompt.py`.

### 4. Agent Development

- **Main agent logic:** Implemented in each `agent.py` under `sub_agents/`.
- **Initial prompt:** Defined in `prompt.py` in each agent folder.
- **Shared code:** Place reusable functions in `library/`.
- **Tools:** Add custom tools in `tools/` and import them in agents as needed.

## Environment Variables

See `.env` for required variables.  
You may need to add additional variables for API keys or custom configurations.

## Contributing

- Add new agents in `sub_agents/` with their own `agent.py` and `prompt.py`.
- Share code via `library/`.
- Document any new environment variables in `.env`.

## License