# Restaurant Finder with AG-UI and CrewAI

This repository contains a complete solution for finding restaurant recommendations using AI agents. It demonstrates the integration of CrewAI with the AG-UI protocol to create interactive, human-in-the-loop AI applications.

## Project Structure

This project consists of two main components:

1. **Backend Agent (`ag-ui-restaurant-agent/`)**: A Python-based AI system using CrewAI for orchestrating multi-agent restaurant search and recommendation workflow.

2. **Frontend Application (`ag-ui-restaurant-frontend/`)**: A Next.js web application that provides a user interface for interacting with the restaurant finder agent.

## Features

- **Restaurant Discovery**: Find restaurants in any location worldwide
- **Real-time Updates**: Follow the agent's progress with live state updates
- **Structured Results**: Receive restaurant information in a consistent, well-organized format
- **Human-In-The-Loop**: Provide feedback on recommendations to get refined suggestions
- **Streaming Responses**: Experience real-time responses as the agent works
- **AG-UI Protocol**: Standardized communication between frontend and backend

## Backend Agent

The backend agent uses CrewAI to coordinate specialized AI agents:

- **Restaurant Research Specialist**: Searches for and gathers details about restaurants
- **Recommendation Specialist**: Creates personalized recommendations based on research

For full details and setup instructions, see the [agent README](./ag-ui-restaurant-agent/README.md).

## Frontend Application

The frontend application provides an intuitive user interface for:

- Entering location queries
- Viewing restaurant recommendations
- Providing feedback to refine recommendations
- Following the agent's progress in real-time

For frontend setup instructions, see the [frontend README](./ag-ui-restaurant-frontend/README.md).

## Getting Started

To run the complete application:

1. **Set Up the Backend Agent**:

   ```powershell
   cd ag-ui-restaurant-agent
   pip install -e .
   # Create .env file with your API keys
   python -m restaurant_finder_agent.main start_api
   ```

2. **Set Up the Frontend Application**:

   ```powershell
   cd ag-ui-restaurant-frontend
   npm install
   npm run dev
   ```

3. **Open your browser** and navigate to `http://localhost:3000`

## Architecture Overview

The application follows a client-server architecture where:

- The backend agent provides a FastAPI server implementing the AG-UI protocol
- The frontend consumes this API using CopilotKit's React components
- Real-time communication happens via Server-Sent Events (SSE)
- State management ensures consistent UX with optimistic updates

## Demo

To test the system quickly, you can run the example client:

```powershell
cd ag-ui-restaurant-agent
python example_client.py
```

## Development

Each component can be developed independently:

- The backend agent can be tested in standalone mode using `python -m restaurant_finder_agent.main`
- The frontend can be developed with mock data in development mode

## License

This project is intended as a demonstration of AI agent technology and CrewAI integration with AG-UI protocol.

## Acknowledgments

- [CrewAI](https://crewai.com) - Multi-agent orchestration framework
- [AG-UI Protocol](https://github.com/microsoft/autogen/blob/main/website/docs/topics/agentchat/agent-ui-protocol.md) - Standardized agent-UI communication protocol
- [CopilotKit](https://copilotkit.ai) - Frontend toolkit for AI agents
