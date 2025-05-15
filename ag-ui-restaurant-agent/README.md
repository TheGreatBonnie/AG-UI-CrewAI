# Restaurant Finder with AG-UI and CrewAI

Welcome to the Restaurant Finder Crew project, powered by [crewAI](https://crewai.com) and integrated with the Agent User Interaction Protocol (AG-UI).

## Project Overview

The Restaurant Finder Agent uses:

- **CrewAI**: For orchestrating a multi-agent workflow to find and recommend restaurants
- **AG-UI Protocol**: To provide a standardized interface for agent communication with real-time updates

## Installation

Ensure you have Python >=3.12.4 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv, or you can use pip for installation:

```bash
pip install -e .
```

Create a `.env` file with your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serperdev_api_key_here
```

## Features

- **Restaurant Search**: Find restaurants in any location
- **Real-time Updates**: Follow the agent's progress with state updates
- **Structured Results**: Receive restaurant information in a structured format
- **Human-In-The-Loop**: Get human feedback on restaurant recommendations
- **Streaming Responses**: Stream results back to your frontend in real-time
- **Agent User Interaction Protocol**: Standardized communication with frontend applications

## Running the Agent

You can run the Restaurant Finder Agent in two modes: standard CrewAI mode or AG-UI API mode.

### Standard Mode (CrewAI)

Run the agent directly using CrewAI:

```powershell
python -m restaurant_finder_agent.main
```

Or with a specific command:

```powershell
python -m restaurant_finder_agent.main run_crew
```

### AG-UI API Mode

Start the AG-UI API server:

```powershell
python -m restaurant_finder_agent.main start_api
```

This will start a FastAPI server at `http://localhost:8000/agent` that follows the AG-UI protocol.

### Example Client

You can test the AG-UI integration with the included example client:

```powershell
python example_client.py
```

This client demonstrates how to connect to the AG-UI endpoint and process real-time events.

## AG-UI Protocol Integration

This project demonstrates how to integrate CrewAI with the AG-UI protocol:

1. **State Management**: Real-time updates on the agent's progress
2. **Tool Calls**: Structured way to invoke tools and functions
3. **Events**: Standardized events for communication between frontend and backend

### Key Components

- **API Endpoint**: FastAPI endpoint following the AG-UI protocol
- **CrewAGUIWrapper**: A wrapper class that bridges CrewAI with AG-UI events
- **State Updates**: JSON Patch format for efficient state updates

## Code Organization

The AG-UI integration is organized as follows:

```
restaurant_finder_agent/
  ├── api.py              # AG-UI protocol FastAPI endpoint
  ├── agui_crew.py        # Wrapper for CrewAI with AG-UI protocol
  ├── crew.py             # CrewAI crew definition
  └── main.py             # Main entry point with start_api command

docs/
  ├── agui_integration_guide.md   # Detailed guide on AG-UI integration
  ├── agui_integration_diagram.md # Architecture diagram (Mermaid)
  └── example_web_client.html     # Example web frontend

example_client.py         # Example Python client for testing
```

## Deploy

The easiest way to deploy your crew is through CrewAI Enterprise, where you can deploy your crew in a few clicks. Simply log in to your CrewAI Enterprise account, navigate to the deployment section, and follow the intuitive steps to get your Restaurant Finder Crew up and running effortlessly. For more details, check out the [crewAI Quickstart Guide](https://docs.crewai.com/quickstart#deploying-your-project).

For deploying with the AG-UI protocol, you'll need to ensure your hosting environment supports FastAPI and Server-Sent Events (SSE).

## Note

CrewAI Enterprise prefers that the Crew code is maintained in a separate repository. Therefore, you will need to provision a separate repository for this folder to ensure proper deployment and management.
