# Human-in-the-Loop AI Workflows with AG-UI and CopilotKit

This guide explains how to implement human-in-the-loop AI workflows using the AG-UI protocol and CopilotKit tools in the Restaurant Finder Agent project.

## What is a Human-in-the-Loop Workflow?

A human-in-the-loop (HITL) workflow combines AI automation with human intervention at strategic points. This approach:

1. Leverages AI's efficiency and scalability
2. Incorporates human judgment, expertise, and decision-making
3. Creates feedback loops that improve AI performance over time

In our Restaurant Finder application, we use HITL to:

- Have AI agents find and analyze restaurant options
- Present recommendations to human users
- Collect feedback from users to refine those recommendations
- Process that feedback with specialized AI agents to provide better results

## Implementation Components

### 1. Backend: AG-UI Protocol Implementation

The backend uses FastAPI to serve an endpoint that follows the AG-UI protocol:

```python
@app.post("/agent")
async def agent_endpoint(input_data: RunAgentInput):
    message_id = str(uuid.uuid4()) # Generate a unique message_id for this run
    encoder = EventEncoder()

    yield encoder.encode(RunStartedEvent(message_id=message_id))
    # ...

    if input_data.feedback:
        # This is a feedback processing request
        async for event in handle_feedback_request(encoder, input_data, message_id, input_data.feedback):
            yield ensure_event_delta(event)
    else:
        # Initial request processing
        # ...
```

### 2. CrewAI Integration

We wrap CrewAI's functionality with AG-UI protocol capabilities using `CrewAGUIWrapper`:

```python
class CrewAGUIWrapper:
    """
    Wrapper class to integrate CrewAI with AG-UI protocol
    """

    def __init__(self, crew_instance, event_callback: Optional[Callable] = None):
        self.crew = crew_instance
        self.event_callback = event_callback
        self.message_id = str(uuid.uuid4())
        # Initialize state...
```

### 3. Frontend: CopilotKit Integration

#### A. State Management with useCoAgent

```tsx
const {
  state,
  stop: stopRestaurantAgent,
  setState,
} = useCoAgent<RestaurantFinderAgentState>({
  name: "restaurantFinderAgent",
  initialState: {
    // Initial state structure
  },
});
```

#### B. Dynamic UI Rendering with useCoAgentStateRender

```tsx
useCoAgentStateRender({
  name: "restaurantFinderAgent",
  handler: ({ nodeName }) => {
    // Event handling logic
  },
  render: ({ status }) => {
    // UI rendering based on agent status
  },
});
```

#### C. Human Feedback Collection with useCopilotAction

```tsx
useCopilotAction({
  name: "provideFeedback",
  description:
    "Allow the user to provide feedback on restaurant recommendations",
  parameters: [
    // Parameter definitions
  ],
  renderAndWaitForResponse: ({ args, respond }) => {
    // Render UI for human feedback and capture response
  },
});
```

#### D. Feedback Processing with useCopilotAction

```tsx
useCopilotAction({
  name: "processFeedback",
  description: "Process user feedback on restaurant recommendations",
  parameters: [
    // Parameter definitions
  ],
  handler: async ({ feedback }) => {
    // Process feedback and update state
  },
});
```

## Step-by-Step Workflow Implementation

### 1. Initial Request Processing

When a user asks for restaurant recommendations:

1. The frontend sends the request to the backend via AG-UI protocol
2. The backend creates a new agent run and initializes state
3. The backend passes the request to CrewAI agents
4. CrewAI orchestrates multiple specialized agents working together:
   - Restaurant Research Specialist: Searches for restaurants
   - Restaurant Recommendation Specialist: Creates personalized recommendations
5. Events are streamed back to the frontend in real-time:
   - Progress updates
   - State changes
   - Agent thoughts and reasoning
   - Tool call events

### 2. Human Feedback Collection

Once restaurant recommendations are ready:

1. The backend sends a `ToolCallStartEvent` and `ToolCallArgsEvent` for `provideFeedback`
2. The frontend renders UI components for human interaction using `renderAndWaitForResponse`
3. The user selects a feedback option
4. The `respond` function sends the feedback back to the agent

```tsx
renderAndWaitForResponse: ({ args, respond }) => {
  const { feedbackOptions, message } = args;

  return (
    <div className="feedback-section mt-6 pt-4 border-t border-gray-200">
      <h3 className="text-lg font-medium mb-3">
        {message || "How do you feel about these recommendations?"}
      </h3>
      <div className="flex flex-wrap gap-2">
        {feedbackOptions.map((option, index) => (
          <button
            key={index}
            onClick={() => {
              // Update UI state
              // Send response back to agent
              respond(option);
            }}>
            {option}
          </button>
        ))}
      </div>
    </div>
  );
};
```

### 3. Feedback Processing

When the user submits feedback:

1. The frontend invokes the `processFeedback` action
2. The action updates the UI state to show processing
3. The backend receives the feedback via a new request
4. The `handle_feedback_request` function processes the feedback
5. CrewAI's Restaurant Recommendation Specialist agent generates refined recommendations
6. Events are streamed back to the frontend with the new recommendations
7. The frontend updates the UI to show the refined results

```python
async def handle_feedback_request(encoder, input_data, message_id, feedback):
    """Handle a feedback request from the user."""
    # Update state for feedback processing
    yield encoder.encode(StateDeltaEvent(...))

    # Process the feedback using CrewAI
    crew_instance = RestaurantFinderTemplateCrew()
    crew_wrapper = CrewAGUIWrapper(crew_instance.crew(), event_callback)
    result = await crew_wrapper.handle_feedback(feedback)

    # Send updated recommendations back to frontend
    # ...
```

## Key Technical Components

### 1. AG-UI Protocol Events

- `RunStartedEvent`: Begins an agent run
- `StateSnapshotEvent` / `StateDeltaEvent`: Updates agent state
- `TextMessageStartEvent` / `TextMessageContentEvent` / `TextMessageEndEvent`: Streams text content
- `ToolCallStartEvent` / `ToolCallArgsEvent` / `ToolCallEndEvent`: Manages tool calls
- `RunFinishedEvent`: Completes an agent run

### 2. CrewAI Integration

- Task Orchestration: Breaking complex workflows into specialized agent tasks
- Crew Kickoff: Executing tasks with appropriate agents
- Result Processing: Parsing, formatting, and returning results to the frontend

### 3. CopilotKit Actions

- `provideFeedback`: Human interface for providing feedback
- `processFeedback`: Action for handling and forwarding feedback to backend
- State Management: Tracking and updating UI state based on agent progress

## Best Practices

1. **State Design**:

   - Design a comprehensive state model that captures all workflow phases
   - Include status information, progress indicators, and UI control flags
   - Use typed interfaces for type safety

2. **Error Handling**:

   - Implement robust error handling in both frontend and backend
   - Provide meaningful error messages to users
   - Gracefully recover from failures

3. **Progress Indication**:

   - Always show the user where they are in the process
   - Indicate when the system is waiting for human input
   - Provide clear feedback when processing user input

4. **User Experience**:

   - Make human interaction points intuitive and clearly marked
   - Provide context for why human input is needed
   - Offer structured input options when possible

5. **Feedback Loops**:
   - Close the loop by showing how user feedback affected results
   - Store feedback for future model improvements
   - Allow iterative refinement through multiple feedback cycles

## Advanced Scenarios

### Multi-Step Human Interaction

For more complex scenarios, you can implement multi-step human interaction:

```tsx
useCopilotAction({
  name: "collectDetailedFeedback",
  renderAndWaitForResponse: ({ args, respond }) => {
    // Step 1: Category selection
    const [step, setStep] = useState(1);
    const [category, setCategory] = useState("");

    if (step === 1) {
      return (
        <CategorySelectionUI
          onSelect={(category) => {
            setCategory(category);
            setStep(2);
          }}
        />
      );
    }

    // Step 2: Detailed feedback
    return (
      <DetailedFeedbackUI
        category={category}
        onSubmit={(details) => {
          respond({ category, details });
        }}
      />
    );
  },
});
```

### Adaptive Agent Behavior

Agents can adapt their behavior based on past human feedback:

```python
async def handle_feedback_request(encoder, input_data, message_id, feedback):
    # Look up user preference history
    user_preferences = await get_user_preferences(input_data.user_id)

    # Augment feedback with preference history
    augmented_inputs = {
        "feedback": feedback,
        "previous_recommendations": previous_recommendations_str,
        "user_preferences": user_preferences
    }

    # Process with preference-aware agent
    result = await crew_wrapper.handle_feedback_with_preferences(augmented_inputs)
    # ...
```

## Conclusion

Human-in-the-loop workflows combine the best of AI automation and human expertise. By implementing these patterns using AG-UI protocol and CopilotKit, you create interactive, adaptive systems that continuously improve through human feedback.

The Restaurant Finder Agent demonstrates this approach by first using AI to search and analyze restaurant options, then gathering human feedback to refine recommendations, creating a more personalized and effective experience.
