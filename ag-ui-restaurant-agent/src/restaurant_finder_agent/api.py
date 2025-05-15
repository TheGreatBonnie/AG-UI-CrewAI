#!/usr/bin/env python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ag_ui.core import ( # type: ignore
    RunAgentInput as BaseRunAgentInput,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent
)
from ag_ui.encoder import EventEncoder # type: ignore
import uuid
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict

from restaurant_finder_agent.crew import RestaurantFinderTemplateCrew

# Extend RunAgentInput to include feedback and original location
class RunAgentInput(BaseRunAgentInput):
    model_config = ConfigDict()
    feedback: str = None
    original_location: str = None  # Add field to hold the original search location

# Create custom event classes for state updates
class StateDeltaEvent(BaseModel):
    model_config = ConfigDict()
    type: str = "STATE_DELTA"
    message_id: str
    delta: list  # JSON Patch format (RFC 6902)

class StateSnapshotEvent(BaseModel):
    model_config = ConfigDict()
    type: str = "STATE_SNAPSHOT"
    message_id: str
    snapshot: Dict[str, Any]  # Complete state object

class ToolCallStartEvent(BaseModel):
    model_config = ConfigDict()
    type: str = "TOOL_CALL_START"
    message_id: str
    toolCallId: str
    toolCallName: str
    tool: str
    delta: str

class ToolCallArgsEvent(BaseModel):
    model_config = ConfigDict()
    type: str = "TOOL_CALL_ARGS"
    message_id: str
    toolCallId: str
    toolCallName: str
    args: Dict[str, Any]
    delta: str

class ToolCallEndEvent(BaseModel):
    model_config = ConfigDict()
    type: str = "TOOL_CALL_END"
    message_id: str
    toolCallId: str
    toolCallName: str
    delta: str

# Note: We've integrated the feedback functionality directly into RunAgentInput
# No longer need a separate FeedbackInput class

app = FastAPI(title="Restaurant Finder AG-UI Endpoint")

# Add CORS middleware for web client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production you should restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_event_delta(event):
    """
    Ensure that all text message events have the required delta parameter.
    AG-UI protocol requires delta field to be a string for TextMessageContentEvent.
    Note: TextMessageEndEvent in this version does not accept a delta parameter.
    
    Args:
        event: Event object to check
        
    Returns:
        Event with delta parameter ensured
    """
    # Check for core AG-UI events that need delta parameter
    if hasattr(event, 'type'):
        if event.type == EventType.TEXT_MESSAGE_CONTENT:
            # Set delta to empty string if it's missing or None
            if not hasattr(event, 'delta') or event.delta is None:
                event.delta = ""
    return event

@app.post("/agent")
async def agent_endpoint(input_data: RunAgentInput):    
    async def event_generator():
        # Create an event encoder to properly format SSE events
        encoder = EventEncoder()        
        
        # Check if this is a feedback request or an initial query
        is_feedback_request = input_data.feedback is not None
        
        # For enhanced debugging
        import uuid
        debug_id = str(uuid.uuid4())[:8]
        
        # Additional check for feedback in message content (for frontend integration)
        if not is_feedback_request and input_data.messages and len(input_data.messages) > 0:
            message_content = input_data.messages[-1].content
            try:
                # Try to parse the message content as JSON
                import json
                feedback_data = json.loads(message_content)
                if isinstance(feedback_data, dict) and ("feedbackText" in feedback_data or "originalLocation" in feedback_data):
                    # This appears to be feedback sent directly in the message content
                    print(f"[{debug_id}] Detected feedback in message content: {message_content}")
                    is_feedback_request = True
                    # Create a properly formatted feedback field
                    input_data.feedback = message_content
                    # If originalLocation is in the JSON, set it in input_data
                    if "originalLocation" in feedback_data:
                        input_data.original_location = feedback_data["originalLocation"]
                        print(f"[{debug_id}] Set original_location from message JSON: {input_data.original_location}")
            except (json.JSONDecodeError, TypeError):
                # Not JSON, treat as regular query
                pass
        
        if is_feedback_request:
            # For feedback requests, use the provided message_id
            message_id = input_data.thread_id  # Using thread_id as message_id
            feedback = input_data.feedback
            print(f"[{debug_id}] DETECTED FEEDBACK REQUEST - Will use Recommendation Specialist")
            print(f"Received feedback request with feedback: '{feedback}'")
            
            # Initialize query
            query = ""
            
            # Try to extract original location from feedback if it's JSON
            try:
                import json
                feedback_data = json.loads(feedback)
                if isinstance(feedback_data, dict) and "originalLocation" in feedback_data:
                    query = feedback_data["originalLocation"]
                    print(f"Extracted original location from feedback JSON: '{query}'")
                    
                    # Also update the input_data.original_location for downstream handlers
                    input_data.original_location = query
            except (json.JSONDecodeError, TypeError):
                print("Feedback is not in JSON format")
            
            # If we couldn't get location from JSON, try the direct field
            if not query:
                query = input_data.original_location if input_data.original_location else ""
                print(f"Original location from input_data: '{query}'")
            
            # If still not available, try thread_state
            if not query and hasattr(input_data, 'thread_state') and input_data.thread_state:
                if 'search' in input_data.thread_state and 'location' in input_data.thread_state['search']:
                    query = input_data.thread_state['search']['location']
                    print(f"Retrieved original location from thread_state: '{query}'")
                    
            print(f"FINAL DECISION: Using location '{query}' for feedback processing")        
            
        else:
            # For initial requests, extract query and create a new message_id
            query = input_data.messages[-1].content
            message_id = str(uuid.uuid4())
            print(f"[{debug_id}] Received initial search query: '{query}' - Will use Research Specialist")# Send run started event
        yield encoder.encode(
            RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )        
        
        # Branch based on whether this is a feedback request or initial query
        if is_feedback_request:
            # For feedback requests, process feedback and exit the generator
            print(f"[{debug_id}] Handling feedback request: '{feedback}'")
            # Make it absolutely clear this is a feedback request in logs
            print(f"[{debug_id}] === PROCESSING FEEDBACK REQUEST WITH RECOMMENDATION SPECIALIST ===")
            # Clear indication we're NOT doing a search
            print(f"[{debug_id}] === BYPASSING SEARCH PHASE AND RESEARCH SPECIALIST ===")
            print(f"\n{'='*80}\nAGENT FLOW DEBUG: Using RECOMMENDATION SPECIALIST for user feedback\n{'='*80}\n")
            
            # Process the feedback with the handle_feedback_request handler
            async for event in handle_feedback_request(encoder, input_data, message_id, feedback):
                yield event
                
            print(f"[{debug_id}] === FEEDBACK PROCESSING COMPLETED ===")
            return  # Explicitly return to prevent fallthrough to the search code
        else:
            # For initial requests, proceed with restaurant search 
            print(f"[{debug_id}] Handling initial search request: '{query}' with Research Specialist")# Send initial state snapshot with two-phase workflow components
            yield encoder.encode(
                StateSnapshotEvent(
                    message_id=message_id,
                    snapshot={
                        "status": {
                            "phase": "initialized",
                            "error": None,
                            "timestamp": datetime.now().isoformat()
                        },
                        "search": {
                            "query": query,
                            "location": query,  # Assuming the query is the location
                            "stage": "not_started",
                            "restaurants_found": 0,
                            "restaurants": [],  # Initialize with empty array
                            "completed": False
                        },                        "processing": {
                            "progress": 0,
                            "phases": ["search", "recommend", "feedback"],  # Task-based workflow
                            "currentPhase": "",
                            "recommendations": None,
                            "completed": False,
                            "inProgress": False,
                            "feedback": None
                        },
                        "ui": {
                            "showRestaurants": False,
                            "showProgress": True,
                            "activeTab": "chat",
                            "showFeedbackPrompt": False,
                            "feedbackOptions": [
                                "Thanks, these look great!",
                                "Can you show me more options?",
                                "Do you have any cheaper restaurants?",
                                "I'd like more fine dining options"
                            ]
                        }
                    }
                )
            )
            
            # Continue with restaurant search
            # Update state, make API calls, etc.
            # Rest of the function for initial requests...
        
        # For initial requests, send initial state snapshot with structured data for restaurant finder workflow
        yield encoder.encode(
            StateSnapshotEvent(
                message_id=message_id,
                snapshot={
                    "status": {
                        "phase": "initialized",
                        "error": None,
                        "timestamp": datetime.now().isoformat()
                    },
                    "search": {
                        "query": query,
                        "location": query,  # Assuming the query is the location
                        "stage": "not_started",
                        "restaurants_found": 0,
                        "restaurants": [],  # Initialize with empty array
                        "completed": False
                    },                    "processing": {
                        "progress": 0,
                        "recommendations": None,
                        "completed": False,
                        "inProgress": False,
                        "feedback": None,
                        "currentPhase": "",
                        "phases": ["search", "recommend", "feedback"]
                    },
                    "ui": {
                        "showRestaurants": False,
                        "showProgress": True,
                        "activeTab": "chat",
                        "showFeedbackPrompt": False,
                        "feedbackOptions": [
                            "Thanks, these look great!",
                            "Can you show me more options?",
                            "Do you have any cheaper restaurants?",
                            "I'd like more fine dining options"
                        ]
                    }
                }
            )
        )        
        
        # Update state for restaurant search started - This is the first phase of our workflow
        yield encoder.encode(
            StateDeltaEvent(
                message_id=message_id,
                delta=[
                    {
                        "op": "replace",                        
                        "path": "/status/phase",
                        "value": "searching_restaurants"
                    },
                    {
                        "op": "replace",
                        "path": "/search/stage",
                        "value": "searching"
                    },
                    {
                        "op": "replace",
                        "path": "/processing/inProgress",
                        "value": True
                    },                    {
                        "op": "replace",
                        "path": "/processing/currentPhase",
                        "value": "search"
                    },
                    {
                        "op": "replace",
                        "path": "/processing/progress",
                        "value": 0.1
                    }
                ]
            )
        )

        # Create an instance of the restaurant finder crew
        crew_instance = RestaurantFinderTemplateCrew()
        
        # Send tool call start event for the search restaurants task        
        tool_call_id = f"call_{str(uuid.uuid4())[:8]}"
        yield encoder.encode(
            ToolCallStartEvent(
                message_id=message_id,
                tool="search_restaurants",
                toolCallId=tool_call_id,
                toolCallName="search_restaurants",
                delta=""  # Required by AG-UI protocol
            )
        )        
        
        # Send tool call args event
        yield encoder.encode(
            ToolCallArgsEvent(
                message_id=message_id,
                toolCallId=tool_call_id,
                toolCallName="search_restaurants",
                args={"location": query},
                delta=""  # Required by AG-UI protocol
            )
        )        
        
        # Send tool call end event
        yield encoder.encode(
            ToolCallEndEvent(
                message_id=message_id,
                toolCallId=tool_call_id,
                toolCallName="search_restaurants",
                delta=""  # Required by AG-UI protocol
            )
        )

        # Update progress
        yield encoder.encode(
            StateDeltaEvent(
                message_id=message_id,
                delta=[
                    {
                        "op": "replace",
                        "path": "/processing/progress",
                        "value": 0.3
                    }
                ]
            )
        )        
        
        # Import our CrewAGUIWrapper
        from restaurant_finder_agent.agui_crew import CrewAGUIWrapper        # Store events that might need to be processed after execution
        events_to_send = []
        
        # We need a non-local function to handle yielding events asynchronously
        async def yield_event(event_obj):
            # Ensure text message events have delta parameter
            event_obj = ensure_event_delta(event_obj)
            try:
                # Encode and yield the event
                encoded_event = encoder.encode(event_obj)
                yield encoded_event
            except Exception as e:
                print(f"Error encoding event: {e}. Event: {event_obj}")
        
        # Define a callback to process events immediately
        def event_callback(event):
            nonlocal events_to_send  # Use this to track if we need extra processing later
            event_type = event.get("type", "")
            
            try:
                if event_type == "STATE_DELTA":
                    # Important state changes need to be sent immediately
                    # Check if this is a phase change that needs to be visible
                    delta = event.get("delta", [])
                    for change in delta:
                        if change.get("path") == "/status/phase":
                            phase = change.get("value")
                            print(f"Phase change detected: {phase}")
                    
                    # Immediately yield the state delta event
                    encoder_event = StateDeltaEvent(
                        message_id=message_id,
                        delta=delta
                    )
                    # We can't yield directly here, so we'll add to events_to_send
                    # but for critical states like phases, we'll ensure they're processed
                    events_to_send.append(encoder_event)
                elif event_type == "TOOL_CALL_START":
                    events_to_send.append(
                        ToolCallStartEvent(
                            message_id=message_id,
                            toolCallId=event.get("toolCallId", ""),
                            toolCallName=event.get("toolCallName", ""),
                            tool=event.get("tool", ""),
                            delta=""  # Required by AG-UI protocol
                        )
                    )
                elif event_type == "TOOL_CALL_ARGS":
                    events_to_send.append(
                        ToolCallArgsEvent(
                            message_id=message_id,
                            toolCallId=event.get("toolCallId", ""),
                            toolCallName=event.get("toolCallName", ""),
                            args=event.get("args", {}),
                            delta=""  # Required by AG-UI protocol
                        )
                    )
                elif event_type == "TOOL_CALL_END":
                    events_to_send.append(
                        ToolCallEndEvent(
                            message_id=message_id,
                            toolCallId=event.get("toolCallId", ""),
                            toolCallName=event.get("toolCallName", ""),
                            delta=""  # Required by AG-UI protocol
                        )
                    )                    
                elif event_type == "TEXT_MESSAGE_START":
                    # Handle text message start events
                    events_to_send.append(
                        TextMessageStartEvent(
                            type=EventType.TEXT_MESSAGE_START,
                            message_id=message_id,
                            role="assistant"  # Required parameter - must specify whether message is from 'assistant' or 'user'
                        )
                    )
                elif event_type == "TEXT_MESSAGE_CONTENT":
                    # Handle text message content events with guaranteed delta
                    delta = event.get("delta", "")  # Default to empty string
                    events_to_send.append(
                        TextMessageContentEvent(
                            type=EventType.TEXT_MESSAGE_CONTENT,
                            message_id=message_id,
                            delta=str(delta)  # Force conversion to string
                        )
                    )                      
                elif event_type == "TEXT_MESSAGE_END":
                    # Handle text message end events
                    # Your version of AG-UI's TextMessageEndEvent does not accept delta parameter
                    events_to_send.append(
                        TextMessageEndEvent(
                            type=EventType.TEXT_MESSAGE_END,
                            message_id=message_id
                        )
                    )
            except KeyError as e:
                print(f"Error handling event: {e}. Event: {event}")
          # Create a wrapper for the crew with our event callback
        crew_wrapper = CrewAGUIWrapper(crew_instance.crew(), event_callback)        # Run the restaurant finder crew with AG-UI integration
        result = await crew_wrapper.run_with_agui({"location": query})
        
        # Parse the results from the crew
        restaurants = crew_wrapper._parse_restaurants(result)
            # Process any queued events that haven't been sent yet
        print(f"Processing {len(events_to_send)} pending events...")
        
        # First, let's identify any state phase events that are critical
        # and make sure they get sent in the correct order with delays
        phase_events = []
        state_events = []
        other_events = []
        
        for event in events_to_send:
            # StateDeltaEvent objects that contain phase changes
            if (isinstance(event, StateDeltaEvent) and 
                any(d.get('path') == '/status/phase' for d in event.delta)):
                phase_events.append(event)
            # Other StateDeltaEvent objects (non-phase changes)
            elif isinstance(event, StateDeltaEvent):
                state_events.append(event)
            # All other event types
            else:
                other_events.append(event)
        
        # Process phase events with delays to ensure visibility
        print(f"Found {len(phase_events)} phase events to process with delays")
        for event in phase_events:
            try:
                # Log the phase change for debugging
                phase_changes = [d for d in event.delta if d.get('path') == '/status/phase']
                for phase_change in phase_changes:
                    print(f"\n=== PROCESSING PHASE CHANGE EVENT: {phase_change.get('value')} ===\n")
                
                # Encode and send the event
                encoded_event = encoder.encode(event)
                yield encoded_event
                
                # Add a significant delay after each phase event
                await asyncio.sleep(1.5)  
                
            except Exception as e:
                print(f"Error encoding phase event: {e}. Event: {event}")
        
        # Then send state events (with shorter delays)
        print(f"Processing {len(state_events)} other state events")
        for event in state_events:
            try:
                encoded_event = encoder.encode(event)
                yield encoded_event
                # Add a small delay between state events
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error encoding state event: {e}. Event: {event}")
        
        # Finally, send all other events
        print(f"Processing {len(other_events)} non-state events")
        for event in other_events:
            try:
                # Ensure that text message events have delta parameter
                event = ensure_event_delta(event)
                encoded_event = encoder.encode(event)
                yield encoded_event
            except Exception as e:
                print(f"Error encoding event: {e}. Event: {event}")
          # Update state with restaurant results - Phase 1 completion
        print("\n=== API: Setting state to 'restaurants_found' phase ===\n")
        rest_found_event = StateDeltaEvent(
            message_id=message_id,
            delta=[
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "restaurants_found"
                },
                {
                    "op": "replace",
                    "path": "/search/stage",
                    "value": "found"
                },
                {
                    "op": "replace",
                    "path": "/search/restaurants_found",
                    "value": len(restaurants)
                },
                {
                    "op": "replace",
                    "path": "/search/restaurants",
                    "value": restaurants
                },
                {
                    "op": "replace",
                    "path": "/ui/showRestaurants",
                    "value": True
                },
                {
                    "op": "replace",
                    "path": "/processing/progress",
                    "value": 0.6
                }
            ]
        )
        yield encoder.encode(rest_found_event)
        
        # Add a delay to ensure state is visible
        await asyncio.sleep(1.5)
        
        # Update state for generating recommendations - Phase 2 start
        print("\n=== API: Setting state to 'presenting_recommendations' phase ===\n")
        recommendations_event = StateDeltaEvent(
            message_id=message_id,
            delta=[
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "presenting_recommendations"
                },
                {
                    "op": "replace",
                    "path": "/processing/currentPhase",
                    "value": "recommendation"
                },
                {
                    "op": "replace",
                    "path": "/processing/progress",
                    "value": 0.7
                }
            ]
        )
        yield encoder.encode(recommendations_event)
        
        # Add a delay to ensure state is visible
        await asyncio.sleep(1.5)
        
        # Update state with recommendations generation complete
        yield encoder.encode(
            StateDeltaEvent(
                message_id=message_id,
                delta=[
                    {
                        "op": "replace",
                        "path": "/status/phase",
                        "value": "await_feedback"
                    },
                    {
                        "op": "replace",
                        "path": "/search/completed",
                        "value": True
                    },
                    {
                        "op": "replace",
                        "path": "/processing/completed",
                        "value": True
                    },
                    {
                        "op": "replace",
                        "path": "/processing/inProgress",
                        "value": False
                    },
                    {
                        "op": "replace",
                        "path": "/processing/progress",
                        "value": 0.95
                    },
                    {
                        "op": "replace",
                        "path": "/processing/recommendations",
                        "value": format_recommendations(result)
                    },
                    {
                        "op": "replace",
                        "path": "/ui/showFeedbackPrompt",
                        "value": True
                    }
                ]
            )        )
        
        # Emit provideFeedback tool call to trigger feedback UI
        tool_call_id = f"call_{str(uuid.uuid4())[:8]}"
        print("Starting provideFeedback tool call with ID:", tool_call_id)
        
        yield encoder.encode(
            ToolCallStartEvent(
                message_id=message_id,
                tool="provideFeedback",
                toolCallId=tool_call_id,
                toolCallName="provideFeedback",
                delta=""
            )
        )
        
        # Create feedback arguments
        feedback_args = {
            "feedbackOptions": [
                "Thanks, these look great!",
                "Can you show me more options?",
                "Do you have any cheaper restaurants?",
                "I'd like more fine dining options"
            ],
            "message": "How do you feel about these recommendations?"
        }
        
        print("Sending provideFeedback tool call args:", feedback_args)
        
        # Send tool call args event with feedback options
        yield encoder.encode(
            ToolCallArgsEvent(
                message_id=message_id,
                toolCallId=tool_call_id,
                toolCallName="provideFeedback",
                args=feedback_args,
                delta=""
            )
        )
        
        # End the tool call before finishing the run
        yield encoder.encode(
            ToolCallEndEvent(
                message_id=message_id,
                toolCallId=tool_call_id,
                toolCallName="provideFeedback",
                delta=""
            )
        )
        
        # Complete the run
        yield encoder.encode(
            RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )

    # Return the streaming response with the generated events outside the generator function
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

async def handle_feedback_request(encoder, input_data, message_id, feedback):
    """
    Handle a feedback request from the user.
    
    Args:
        encoder: EventEncoder for encoding events
        input_data: The RunAgentInput with feedback data
        message_id: The message ID for this interaction
        feedback: The feedback text provided by the user
        
    Returns:
        Generator yielding encoded events
    """
    print(f"Starting handle_feedback_request with feedback: '{feedback}'")
    print("*** IMPORTANT: This is a FEEDBACK request, NOT a search request ***")
      # Create initial state structure based on thread_state if available
    initial_state = {
        "status": {
            "phase": "initialized",
            "error": None,
            "timestamp": datetime.now().isoformat()
        },
        "search": {
            "query": "",
            "location": "",
            "stage": "not_started",
            "restaurants_found": 0,
            "restaurants": [],
            "completed": False
        },
        "processing": {
            "progress": 0,
            "recommendations": None,
            "completed": False,
            "inProgress": False,
            "feedback": None,
            "currentPhase": "",
            "phases": ["search", "recommend", "feedback"]
        },
        "ui": {
            "showRestaurants": False,
            "showProgress": True,
            "activeTab": "chat",
            "showFeedbackPrompt": False,
            "feedbackOptions": [
                "Thanks, these look great!",
                "Can you show me more options?",
                "Do you have any cheaper restaurants?",
                "I'd like more fine dining options"
            ]
        }
    }
    
    # Check if we have thread_state with previous recommendations
    stored_recommendations = None
    if hasattr(input_data, 'thread_state') and input_data.thread_state:
        try:
            thread_state = json.loads(input_data.thread_state) if isinstance(input_data.thread_state, str) else input_data.thread_state
            if isinstance(thread_state, dict):
                # Extract recommendations if available
                if thread_state.get("processing", {}).get("recommendations"):
                    stored_recommendations = thread_state["processing"]["recommendations"]
                    initial_state["processing"]["recommendations"] = stored_recommendations
                    print(f"Found stored recommendations in thread_state, length: {len(stored_recommendations)}")
                    print(f"Preview: {stored_recommendations[:100]}...")
                
                # Also restore location if available
                if thread_state.get("search", {}).get("location"):
                    initial_state["search"]["location"] = thread_state["search"]["location"]
                    print(f"Restored location from thread_state: {initial_state['search']['location']}")
                
                # Preserve other important state elements
                if thread_state.get("search", {}).get("restaurants"):
                    initial_state["search"]["restaurants"] = thread_state["search"]["restaurants"]
                    initial_state["search"]["restaurants_found"] = len(thread_state["search"]["restaurants"])
                    print(f"Restored {initial_state['search']['restaurants_found']} restaurants from thread_state")
        except Exception as e:
            print(f"Error processing thread_state: {e}")
    
    # Send the state snapshot
    yield encoder.encode(
        StateSnapshotEvent(
            message_id=message_id,
            snapshot=initial_state
        )
    )
      
    # Initialize feedback_text and original_location to default values
    feedback_text = feedback
    original_location = ""
    
    # Try to parse feedback as JSON to extract original location
    try:
        import json
        feedback_data = json.loads(feedback)
        if isinstance(feedback_data, dict) and "originalLocation" in feedback_data:
            original_location = feedback_data["originalLocation"]
            # Extract feedback text if available
            if "feedbackText" in feedback_data:
                feedback_text = feedback_data["feedbackText"]
            print(f"Successfully parsed feedback JSON. Original location: '{original_location}', Feedback: '{feedback_text}'")
    except (json.JSONDecodeError, TypeError):
        print("Feedback is not in JSON format")
    
    # Check if thread_id exists - this is needed to preserve the original query context
    if not input_data.thread_id:
        print("Warning: No thread_id found in input_data, may cause context loss")
          
    # Check what the last message content was in case we need it for context
    last_message_content = ""
    if input_data.messages and len(input_data.messages) > 0:
        last_message_content = input_data.messages[-1].content
        print(f"Last message in thread was: '{last_message_content}'")
          # If we haven't extracted feedback_text yet, use the last message content as fallback
        if not feedback_text or feedback_text == feedback:
            feedback_text = last_message_content
            print(f"Using last message content as feedback text: '{feedback_text}'")
        
        # Update state for feedback processing started - explicitly show we're using Recommendation Specialist    
        yield encoder.encode(
        StateDeltaEvent(
            message_id=message_id,
            delta=[
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "processing_feedback"
                },
                {
                    "op": "replace",
                    "path": "/processing/inProgress",
                    "value": True
                },
                {
                    "op": "replace",
                    "path": "/processing/currentPhase",
                    "value": "feedback" 
                },
                {
                    "op": "replace",
                    "path": "/processing/progress",
                    "value": 0.7
                },
                
            ]
        )
    )
    
    # Create an instance of the restaurant finder crew
    crew_instance = RestaurantFinderTemplateCrew()
    
    # Import our CrewAGUIWrapper
    from restaurant_finder_agent.agui_crew import CrewAGUIWrapper
    
    # Store events that need to be sent
    events_to_send = []
      # Define a callback to store events          
    def event_callback(event):
        event_type = event.get("type", "")
        try:
            if event_type == "STATE_SNAPSHOT":
                # Handle state snapshot events - these establish the base state structure
                events_to_send.append(
                    StateSnapshotEvent(
                        message_id=message_id,
                        snapshot=event.get("snapshot", {})
                    )
                )
            elif event_type == "STATE_DELTA":
                events_to_send.append(
                    StateDeltaEvent(
                        message_id=message_id,
                        delta=event.get("delta", [])
                    )
                )
            elif event_type == "TOOL_CALL_START":
                events_to_send.append(
                    ToolCallStartEvent(
                        message_id=message_id,
                        toolCallId=event.get("toolCallId", ""),
                        toolCallName=event.get("toolCallName", ""),
                        tool=event.get("tool", ""),
                        delta=""  # Required by AG-UI protocol
                    )
                )
            elif event_type == "TOOL_CALL_ARGS":
                events_to_send.append(
                    ToolCallArgsEvent(
                        message_id=message_id,
                        toolCallId=event.get("toolCallId", ""),
                        toolCallName=event.get("toolCallName", ""),
                        args=event.get("args", {}),
                        delta=""  # Required by AG-UI protocol
                    )
                )
            elif event_type == "TOOL_CALL_END":
                events_to_send.append(
                    ToolCallEndEvent(
                        message_id=message_id,
                        toolCallId=event.get("toolCallId", ""),
                        toolCallName=event.get("toolCallName", ""),
                        delta=""  # Required by AG-UI protocol
                    )
                )                    
            elif event_type == "TEXT_MESSAGE_START":
                events_to_send.append(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=message_id,
                        role="assistant"
                    )
                )
            elif event_type == "TEXT_MESSAGE_CONTENT":
                delta = event.get("delta", "")
                events_to_send.append(
                    TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        delta=str(delta)
                    )
                )                      
            elif event_type == "TEXT_MESSAGE_END":
                events_to_send.append(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END,
                        message_id=message_id
                    )
                )
        except KeyError as e:
            print(f"Error handling event: {e}. Event: {event}")
              # Create a wrapper for the crew with our event callback
    print("Creating CrewAGUIWrapper for feedback processing")
    crew_wrapper = CrewAGUIWrapper(crew_instance.crew(), event_callback)
      # Process thread_state to extract important information
    if hasattr(input_data, 'thread_state') and input_data.thread_state:
        try:
            # Ensure thread_state is properly parsed
            thread_state = input_data.thread_state
            if isinstance(thread_state, str):
                thread_state = json.loads(thread_state)
            
            print("\n===== DEEP THREAD STATE ANALYSIS =====")
            
            # Preserve the original search query/location in the wrapper's state
            if thread_state.get('search', {}).get('location'):
                original_location = thread_state['search']['location']
                print(f"Preserved original search location from thread state: '{original_location}'")
                crew_wrapper.state["search"]["location"] = original_location
                crew_wrapper.state["search"]["query"] = original_location
            else:
                print("WARNING: No location found in thread_state.search")
                
            # Log thread_state structure for debugging
            print("Thread state structure:", list(thread_state.keys()))
            if 'processing' in thread_state:
                print("Processing state structure:", list(thread_state['processing'].keys()))
            
            # CRITICAL FIX: Restore the original recommendations directly to the wrapper state
            if thread_state.get('processing', {}).get('recommendations'):
                previous_recommendations = thread_state['processing']['recommendations']
                print(f"Found previous recommendations in thread_state: {len(previous_recommendations)} characters")
                print(f"Preview: {previous_recommendations[:100]}...")
                
                # Store recommendations in multiple places for redundancy
                crew_wrapper.state["processing"]["recommendations"] = previous_recommendations
                crew_wrapper.original_recommendations = previous_recommendations  # Store in a dedicated attribute
                
                # Check if recommendations mention the location
                if original_location:
                    location_parts = original_location.lower().split(',')[0].strip()
                    if location_parts and location_parts in previous_recommendations.lower():
                        print(f"✓ Verified: Original location '{location_parts}' is mentioned in the recommendations")
                    else:
                        print(f"WARNING: Original location '{location_parts}' not found in recommendations!")
            else:
                print("WARNING: No recommendations found in thread_state.processing")
            
            # Also restore restaurant list if available
            if thread_state.get('search', {}).get('restaurants'):
                crew_wrapper.state["search"]["restaurants"] = thread_state['search']['restaurants']
                crew_wrapper.state["search"]["restaurants_found"] = len(thread_state['search']['restaurants'])
                print(f"Restored {len(thread_state['search']['restaurants'])} restaurants from thread_state")
                
                # Store a backup of the restaurants too
                crew_wrapper.original_restaurants = thread_state['search']['restaurants']
            
            print("===== END THREAD STATE ANALYSIS =====\n")
        except Exception as e:
            print(f"Error processing thread_state: {e}")
            import traceback
            traceback.print_exc()
      # Send tool call start event for processing feedback
    tool_call_id = f"call_{str(uuid.uuid4())[:8]}"
    yield encoder.encode(
        ToolCallStartEvent(
            message_id=message_id,
            tool="provideFeedback",
            toolCallId=tool_call_id,
            toolCallName="provideFeedback",
            delta=""
        )
    )
      # Send tool call args event
    yield encoder.encode(
        ToolCallArgsEvent(
            message_id=message_id,
            toolCallId=tool_call_id,
            toolCallName="provideFeedback",
            args={
                "feedbackOptions": [
                    "Thanks, these look great!",
                    "Can you show me more options?",
                    "Do you have any cheaper restaurants?",
                    "I'd like more fine dining options"
                ],
                "message": "How do you feel about these recommendations?"
            },
            delta=""
        )
    )      
    print(f"About to process feedback via handle_feedback: '{feedback}'")
      # Try to parse the feedback if it's in JSON format (might contain original location)
    # Note: We already initialized these variables above, but we'll refine them here
    try:
        # Check if feedback contains JSON with originalLocation field
        import json
        feedback_data = json.loads(feedback)
        if isinstance(feedback_data, dict):
            # Check for different field name variations
            if "originalLocation" in feedback_data:
                original_location = feedback_data["originalLocation"]
                print(f"Extracted original location from feedbackText.originalLocation: '{original_location}'")
            elif "original_location" in feedback_data:
                original_location = feedback_data["original_location"]
                print(f"Extracted original location from feedbackText.original_location: '{original_location}'")
                
            # Extract the actual feedback text
            if "feedbackText" in feedback_data:
                feedback_text = feedback_data["feedbackText"]
                print(f"Extracted feedback text from feedbackText: '{feedback_text}'")
            elif "feedback" in feedback_data:
                feedback_text = feedback_data["feedback"]
                print(f"Extracted feedback text from feedback: '{feedback_text}'")
            
            print(f"Successfully parsed feedback JSON with: location='{original_location}', feedback='{feedback_text}'")
    except (json.JSONDecodeError, TypeError):
        # Not JSON or not properly formatted, use as is
        print("Feedback is not in JSON format, using as plain text")
    
    # For critical debugging
    print("================================================")
    print(f"FEEDBACK PROCESSING VARIABLES:")
    print(f"  Original Location: '{original_location}'")
    print(f"  Feedback Text: '{feedback_text}'")
    if hasattr(input_data, 'original_location') and input_data.original_location:
        print(f"  Input Data Original Location: '{input_data.original_location}'")
    if hasattr(input_data, 'thread_state') and input_data.thread_state:
        if 'search' in input_data.thread_state and 'location' in input_data.thread_state['search']:
            print(f"  Thread State Location: '{input_data.thread_state['search']['location']}'")
    print("================================================")
      # Our priority is to use original_location from the feedback JSON or input_data
    # Initial state setup before calling handle_feedback
    location_to_use = ""
    
    # Priority 1: JSON extracted location
    if original_location:
        location_to_use = original_location
        print(f"Using location from JSON: '{location_to_use}'")
    
    # Priority 2: input_data.original_location
    elif hasattr(input_data, 'original_location') and input_data.original_location:
        location_to_use = input_data.original_location
        print(f"Using location from input_data: '{location_to_use}'")
    
    # Priority 3: thread_state location
    elif hasattr(input_data, 'thread_state') and input_data.thread_state:
        if 'search' in input_data.thread_state and 'location' in input_data.thread_state['search']:
            location_to_use = input_data.thread_state['search']['location']
            print(f"Using location from thread_state: '{location_to_use}'")
    
    # Now update the crew_wrapper's state with the determined location
    if location_to_use:
        print(f"*** IMPORTANT: Setting crew_wrapper state location to '{location_to_use}' ***")        # Make a proper deep copy of the state with all required structures
        new_state = {
            "status": crew_wrapper.state.get("status", {
                "phase": "await_feedback",
                "error": None,
                "timestamp": datetime.now().isoformat()
            }),
            "search": {
                "location": location_to_use,
                "query": location_to_use,  # Set both location and query
                "restaurants": crew_wrapper.state.get("search", {}).get("restaurants", []),
                "restaurants_found": crew_wrapper.state.get("search", {}).get("restaurants_found", 0),
                "stage": crew_wrapper.state.get("search", {}).get("stage", "feedback"),
                "completed": crew_wrapper.state.get("search", {}).get("completed", True)
            },
            "processing": crew_wrapper.state.get("processing", {
                "progress": 0.66,
                "recommendations": "",
                "completed": False,
                "inProgress": False,
                "feedback": None,
                "currentPhase": "feedback",
                "phases": ["search", "recommend", "feedback"]
            }),
            "ui": crew_wrapper.state.get("ui", {
                "showRestaurants": True,
                "showProgress": True,
                "activeTab": "chat",
                "showFeedbackPrompt": True
            })
        }
        crew_wrapper.state = new_state    # Process the feedback - make sure handle_feedback doesn't trigger a new search
    # Send the decoded feedback directly to handle_feedback without re-encoding
    # This prevents double-JSON encoding issues
    print(f"Directly sending feedback_text: '{feedback_text}' and location: '{location_to_use}'")
      # Create a simple direct structure for handle_feedback
    direct_feedback = {
        "feedbackText": feedback_text,
        "originalLocation": location_to_use
    }
      # Explicitly indicate we're using recommendation specialist for feedback
    print("*** USING RECOMMENDATION SPECIALIST TO HANDLE FEEDBACK ***")
    print(f"Sending to handle_feedback: feedbackText='{feedback_text}', originalLocation='{location_to_use}'")
    result = await crew_wrapper.handle_feedback(direct_feedback)
    
    # Debug output to see what we got back
    print(f"Result from handle_feedback: {type(result).__name__}")
    if hasattr(result, 'raw'):
        print(f"Result.raw length: {len(result.raw)}")
    elif hasattr(result, '__str__'):
        print(f"Result.__str__ length: {len(str(result))}")
      
    # Send tool call end event
    yield encoder.encode(
        ToolCallEndEvent(
            message_id=message_id,
            toolCallId=tool_call_id,
            toolCallName="provideFeedback",
            delta=""
        )
    )
    
    # Send any events collected during execution
    for event in events_to_send:
        try:
            event = ensure_event_delta(event)
            encoded_event = encoder.encode(event)
            yield encoded_event
        except Exception as e:
            print(f"Error encoding event: {e}. Event: {event}")    # Format the result properly
    formatted_result = ""
    if hasattr(result, 'raw'):
        formatted_result = result.raw
        print(f"Using result.raw for formatted_result, length: {len(formatted_result)}")
    elif hasattr(result, '__str__'):
        formatted_result = str(result)
        print(f"Using string conversion for formatted_result, length: {len(formatted_result)}")
    else:
        formatted_result = "No feedback response available"
        print("Warning: No proper result data available for formatted_result")
    
    # Send text event to explain this is from the Recommendation Specialist
    yield encoder.encode(
        TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant"
        )
    )
      # Make it crystal clear we're using the Recommendation Specialist with a more personalized message
    prefix_message = "💬 [Restaurant Recommendation Specialist]\nThank you for your feedback! I'm here to help you find the perfect dining experience."
    
    yield encoder.encode(
        TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=f"{prefix_message}\n\n"
        )
    )
    
    yield encoder.encode(
        TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
    )    # Update final state - clearly mark that feedback was handled by Recommendation Specialist
    yield encoder.encode(
        StateDeltaEvent(
            message_id=message_id,
            delta=[
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "feedback_completed"
                },
                {
                    "op": "replace",
                    "path": "/processing/completed",
                    "value": True
                },
                {
                    "op": "replace",
                    "path": "/processing/inProgress",
                    "value": False
                },
                {
                    "op": "replace",
                    "path": "/processing/progress",
                    "value": 1.0
                },
                {
                    "op": "replace",
                    "path": "/processing/currentPhase", 
                    "value": "feedback_complete"
                },
                               
                {
                    "op": "replace",
                    "path": "/processing/recommendations",
                    "value": formatted_result
                },
                {
                    "op": "replace",
                    "path": "/ui/showFeedbackPrompt",
                    "value": False
                },
            ]
        )
    )
    
    # Complete the run
    yield encoder.encode(
        RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        )
    )

def parse_crew_results(result):
    """
    Parse the CrewAI results into a structured format for the frontend
    This function would extract restaurant information from the CrewAI output
    """
    # This is a placeholder implementation
    # You would need to parse the actual output from your crew
    restaurants = []
    
    try:
        # Example parsing - modify based on your actual result structure
        lines = result.split('\n')
        current_restaurant = {}
        
        for line in lines:
            if '**Restaurant' in line and 'Name' in line:
                if current_restaurant and 'name' in current_restaurant:
                    restaurants.append(current_restaurant)
                current_restaurant = {'id': f'rest_{len(restaurants)}'}
                name_part = line.split('**Restaurant Name**: ')[1].strip() if '**Restaurant Name**: ' in line else line.split(':')[1].strip()
                current_restaurant['name'] = name_part
            elif '**Cuisine**:' in line:
                current_restaurant['cuisine'] = line.split('**Cuisine**:')[1].strip()
            elif '**Price Range**:' in line:
                current_restaurant['priceRange'] = line.split('**Price Range**:')[1].strip()
            elif '**Ratings**:' in line:
                current_restaurant['rating'] = line.split('**Ratings**:')[1].strip()
            elif '**Signature Dishes**:' in line:
                current_restaurant['signatureDishes'] = line.split('**Signature Dishes**:')[1].strip()
        
        # Don't forget the last restaurant
        if current_restaurant and 'name' in current_restaurant:
            restaurants.append(current_restaurant)
    except Exception as e:
        # Fall back to a simple format if parsing fails
        restaurants.append({
            'id': 'rest_fallback',
            'name': 'See detailed recommendations below',
            'cuisine': 'Various',
            'priceRange': 'Various',
            'rating': 'Various'
        })
    
    return restaurants

def format_recommendations(result):
    """
    Format the crew results into a nicely structured recommendation format
    """
    # If result is a CrewOutput object, extract the raw text
    if hasattr(result, 'raw'):
        return result.raw
    # If it's already a string or can be converted to string
    elif hasattr(result, '__str__'):
        return str(result)
    # Fallback
    else:
        return "No structured recommendations available"

def start_server():
    """Run the uvicorn server."""
    import uvicorn # type: ignore
    uvicorn.run("restaurant_finder_agent.api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
