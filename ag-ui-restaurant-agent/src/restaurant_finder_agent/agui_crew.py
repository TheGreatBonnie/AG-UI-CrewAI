"""
AG-UI integration for CrewAI
This module provides classes and utilities to integrate CrewAI with AG-UI protocol
"""

from crewai import Agent, Task, Crew, Process
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel
import uuid
from datetime import datetime
import asyncio

class CrewAGUIWrapper:
    """
    Wrapper class to integrate CrewAI with AG-UI protocol
    This allows for real-time observability and state management when running CrewAI tasks
    """
    def __init__(self, crew_instance, event_callback: Optional[Callable] = None):
        """
        Initialize the wrapper with a CrewAI crew instance and an optional callback for events
        
        Args:
            crew_instance: A CrewAI Crew instance
            event_callback: Optional callback function that will be called with AG-UI protocol events
        """
        self.crew = crew_instance
        self.event_callback = event_callback
        self.message_id = str(uuid.uuid4())
        # Dedicated attributes for storing original data separately from state
        self.original_recommendations = None
        self.original_location = None
        self.original_restaurants = []
        
        self.state = {
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
                    "Thanks for the recommendations! These look perfect.",
                    "Can you suggest more restaurants with different cuisines?",
                    "I'm looking for more budget-friendly dining options.",
                    "I prefer upscale fine dining experiences. Any suggestions?",
                    "Are there any restaurants with unique dining experiences?"
                ]
            }
        }
        
        # Hook into CrewAI events if possible
        # This is a placeholder for future CrewAI event integration
    async def run_with_agui(self, inputs: Dict[str, Any]):
        """
        Run the CrewAI crew with AG-UI protocol integration following the CrewAI task workflow:
        1. search_restaurants_task: Restaurant Research Specialist gathers detailed information
        2. present_recommendations_task: Restaurant Recommendation Specialist formats results
        3. respond_to_feedback_task: Handle user feedback on recommendations (called separately)
        
        Args:
            inputs: Input parameters for the CrewAI crew
            
        Returns:
            The result from the CrewAI crew
        """
        # Initialize state
        self._update_state([
            {
                "op": "replace",
                "path": "/status/phase",
                "value": "initialized"
            },
            {
                "op": "replace",
                "path": "/search/stage",
                "value": "searching"
            },
            {
                "op": "replace",
                "path": "/search/query",
                "value": inputs.get("location", "")
            },
            {
                "op": "replace",
                "path": "/search/location",
                "value": inputs.get("location", "")
            },
            {
                "op": "replace",
                "path": "/processing/inProgress",
                "value": True
            },
            {
                "op": "replace",
                "path": "/processing/progress",
                "value": 0.1
            }
        ])
        
        # Allow a brief delay for initialization state to register
        await asyncio.sleep(0.5)
        try:
            # Find all tasks in the crew
            search_task = None
            recommendations_task = None
            feedback_task = None
            
            for task in self.crew.tasks:
                # Use string representation to identify tasks since config might not be directly accessible
                task_str = str(task)
                if 'search_restaurants_task' in task_str:
                    search_task = task
                elif 'present_recommendations_task' in task_str:
                    recommendations_task = task
                elif 'respond_to_feedback_task' in task_str:
                    feedback_task = task
            
            if not search_task or not recommendations_task:
                raise ValueError("Required tasks not found in the crew")
                
            # TASK 1: Search Restaurants
            self._emit_text_message("🔍 Starting restaurant search in " + inputs.get("location", ""))
            self._emit_tool_call("search_restaurants_task", {"location": inputs.get("location", "")}, "search")
              
            self._update_state([
                {
                    "op": "replace",
                    "path": "/status/phase", 
                    "value": "searching_restaurants"
                },
                {
                    "op": "replace",
                    "path": "/processing/progress", 
                    "value": 0.25
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
                },
                {
                    "op": "replace",
                    "path": "/processing/currentPhase",
                    "value": "search"
                },
                {
                    "op": "replace",
                    "path": "/search/restaurants_found",
                    "value": 0
                }
            ])
            
            # Execute the restaurant search task
            self._emit_text_message("🔎 The Restaurant Research Specialist is searching for top restaurants...")
            
            # Create a new Crew instance with just the search task
            search_crew = Crew(
                agents=[search_task.agent],
                tasks=[search_task],
                verbose=True
            )
            
            # Execute the crew with just the search task
            search_result = await asyncio.to_thread(search_crew.kickoff, inputs)
            
            # Parse the results to extract restaurant information
            restaurants = self._parse_restaurants(search_result)
            self._emit_text_message(f"🍽️ Found {len(restaurants)} restaurants in {inputs.get('location', '')}!")
              # Update state with search results - Important to show "restaurants_found" phase
            print("Setting state to 'restaurants_found' phase...")
            
            self._update_state([
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
                    "value": 0.5
                }
            ])
            
            # Important: Add delay to ensure state is visible in UI
            await asyncio.sleep(1.5)
              
            # TASK 2: Present Recommendations
            # Convert search result string for tool call emission to match what we'll pass to the task
            search_result_str = ""
            if hasattr(search_result, 'raw'):
                search_result_str = search_result.raw
            elif hasattr(search_result, '__str__'):
                search_result_str = str(search_result)
            else:
                search_result_str = "No results available"
            
            self._emit_tool_call("present_recommendations_task", 
                                {"location": inputs.get("location", ""), "restaurant_data": search_result_str}, 
                                "recommend")
            
            self._emit_text_message("✨ Creating personalized restaurant recommendations...")            # Update state to indicate we're presenting recommendations
            print("Setting state to 'presenting_recommendations' phase...")
            
            self._update_state([
                {
                    "op": "replace",
                    "path": "/status/phase", 
                    "value": "presenting_recommendations"
                },
                {
                    "op": "replace",
                    "path": "/processing/progress",
                    "value": 0.7
                },
                {
                    "op": "replace",
                    "path": "/processing/currentPhase",
                    "value": "recommend"
                }
            ])
            
            # Important: Add delay to ensure the presenting_recommendations state is visible in UI
            await asyncio.sleep(2.0)
              # Execute the recommendations task
            # We've already converted the search_result to a string above
            
            recommendations_inputs = {
                "location": inputs.get("location", ""),
                "restaurant_data": search_result_str  # Pass the search results as a string
            }
            
            
            
            # Create a new Crew instance with just the recommendations task
        
            recommendations_crew = Crew(
                agents=[recommendations_task.agent],
                tasks=[recommendations_task],
                verbose=True,  
            )
              # Execute the crew with just the recommendations task
           
            recommendations_result = await asyncio.to_thread(recommendations_crew.kickoff, recommendations_inputs)
            
            task_output = recommendations_task.output
            
            # Format the recommendation results to a string
            result_text = ""
            if hasattr(recommendations_result, 'raw'):
                result_text = recommendations_result.raw
            elif hasattr(recommendations_result, '__str__'):
                result_text = str(recommendations_result)
            else:
                result_text = "No recommendations available"            # CRITICAL FIX: Better store and update final state with recommendations
            # Store deep copy of the recommendations for use in feedback
            original_recommendations = result_text
            
            # Store recommendations in multiple places for redundancy
            self.original_recommendations = original_recommendations
            self.original_location = inputs.get("location", "")
            
            # Get the location for validation
            location = inputs.get("location", "")
            location_parts = location.lower().split(',')[0].strip() if location else ""
            
            # Print clear debug information
            print(f"\n=== STORING ORIGINAL RECOMMENDATIONS ===")
            print(f"For location: '{location}', primary city: '{location_parts}'")
            print(f"Length: {len(original_recommendations)}")
            print(f"Preview: {original_recommendations[:200]}...")
            
            # Verify location is mentioned in recommendations
            if location_parts and len(location_parts) > 2:
                if location_parts in original_recommendations.lower():
                    print(f"✓ VERIFIED: Location '{location_parts}' is mentioned in recommendations")
                else:
                    print(f"⚠️ WARNING: Location '{location_parts}' NOT found in recommendations!")
                    
            print(f"=== END OF RECOMMENDATIONS PREVIEW ===\n")
            
            # Update final state with recommendations complete
            self._update_state([
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
                    "value": 1.0
                },
                {
                    "op": "replace",
                    "path": "/processing/recommendations",
                    "value": original_recommendations  # Store the original formatted recommendations
                },
                {
                    "op": "replace",
                    "path": "/ui/showFeedbackPrompt",
                    "value": True
                }
            ])
            
            # Send message following AG-UI protocol with the already formatted result_text
            self._emit_text_message(result_text)            
            
            # Explicitly emit a tool call to trigger the feedback UI component in CopilotKit with personalized message
            self._emit_tool_call("provideFeedback", {
                "feedbackOptions": self.state["ui"]["feedbackOptions"],
                "message": "I've curated these restaurant recommendations based on my expertise. What do you think of these options?"
            }, "feedback")
            
            return recommendations_result
        
        except Exception as e:
            # Update state with error
            self._update_state([
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "error"
                },
                {
                    "op": "replace",
                    "path": "/status/error",
                    "value": str(e)
                },
                {
                    "op": "replace",
                    "path": "/processing/inProgress",
                    "value": False
                }
            ])
            raise e
    async def handle_feedback(self, feedback):
        """
        Process user feedback to restaurant recommendations using the respond_to_feedback_task
        This function ensures feedback is ALWAYS handled by the Recommendation Specialist,
        not the Research Specialist.
        
        Args:
            feedback: Can be a string (JSON or plain text) or a dictionary with feedbackText and originalLocation
            
        Returns:
            Additional recommendations or closing message
        """        
        # Super clear debug message to ensure we're handling feedback correctly
        print(f"\n{'*'*80}")
        print(f"*** HANDLING FEEDBACK WITH RECOMMENDATION SPECIALIST (NOT a new search) ***")
        print(f"*** Feedback received: '{feedback}' (type: {type(feedback).__name__}) ***")
        print(f"{'*'*80}\n")# Try to parse feedback and extract required information
        original_location = self.state.get("search", {}).get("location", "")
        feedback_text = ""
        
        # Handle the case where feedback is already a dictionary (direct structure)
        if isinstance(feedback, dict):
            feedback_text = feedback.get("feedbackText", "")
            if "originalLocation" in feedback and feedback["originalLocation"]:
                original_location = feedback["originalLocation"]
            print(f"Received direct feedback dictionary - text: '{feedback_text}', location: '{original_location}'")
            return await self._process_feedback(feedback_text, original_location)
        
        # Otherwise treat as string that might be JSON
        feedback_text = feedback
        try:
            import json
            print(f"DEBUG - Raw feedback received: {feedback}")
            feedback_data = json.loads(feedback)
            if isinstance(feedback_data, dict):
                if "feedbackText" in feedback_data:
                    feedback_text = feedback_data["feedbackText"]
                    print(f"Extracted feedback text from JSON: '{feedback_text}'")
                if "originalLocation" in feedback_data:
                    # Direct extraction of location
                    original_location = feedback_data["originalLocation"]
                    print(f"Extracted original location from JSON: '{original_location}'")
                    
                    # Update state with the original location to ensure it's used for feedback
                    if original_location and len(original_location.strip()) > 0:
                        print(f"*** SETTING LOCATION IN STATE: '{original_location}' ***")
                        self._update_state([{
                            "op": "replace",
                            "path": "/search/location",
                            "value": original_location
                        }])
            # Store the extracted values for later use
            feedback = feedback_text  # Use the extracted text as feedback
            
            # Extra debug logging
            print(f"DEBUG - Final values after parsing:")
            print(f"  feedback_text: '{feedback_text}'")
            print(f"  original_location: '{original_location}'") 
            print(f"  state location: '{self.state.get('search', {}).get('location', '')}'")
            print(f"  Will use feedback_text for processing feedback")
        except (json.JSONDecodeError, TypeError):
            print("Feedback is not in JSON format, using as plain text")
        return await self._process_feedback(feedback_text, original_location)
    
    async def _process_feedback(self, feedback_text, original_location):
        """
        Internal helper method to process feedback after parsing
        
        Args:
            feedback_text: The extracted feedback text
            original_location: The original location for context
            
        Returns:
            Processed recommendations based on feedback
        """
        # Update state to indicate processing feedback
        self._update_state([
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
                "path": "/processing/progress",
                "value": 0.7
            },
            {
                "op": "replace",
                "path": "/processing/feedback",
                "value": feedback_text
            },
            {
                "op": "replace", 
                "path": "/search/location",
                "value": original_location
            }
        ])        # IMPROVED RECOMMENDATION RETRIEVAL: Multiple sources with sophisticated fallback mechanisms
        previous_recommendations_str = ""
        
        print("\n===== RETRIEVING RECOMMENDATIONS =====")
        # Source 0: Dedicated attribute (highest priority)
        if self.original_recommendations is not None and len(self.original_recommendations) > 100:
            previous_recommendations_str = self.original_recommendations
            print(f"SUCCESS: Retrieved recommendations from dedicated attribute: {len(previous_recommendations_str)} characters")
        else:
            print("No recommendations found in dedicated attribute, checking state...")
            
            # Source 1: Direct from state
            previous_recommendations = self.state.get("processing", {}).get("recommendations")
            
            if previous_recommendations is not None and previous_recommendations != "None" and (
                isinstance(previous_recommendations, str) and len(previous_recommendations.strip()) > 100
            ):
                # We have valid recommendations stored in processing.recommendations
                previous_recommendations_str = previous_recommendations
                print(f"FOUND RECOMMENDATIONS in state.processing.recommendations: {len(previous_recommendations_str)} characters")
            else:
                print(f"No valid recommendations in state.processing.recommendations, checking alternatives...")
                
                # Source 2: Convert CrewOutput if needed
                if previous_recommendations is not None and (hasattr(previous_recommendations, 'raw') or hasattr(previous_recommendations, '__str__')):
                    if hasattr(previous_recommendations, 'raw'):
                        previous_recommendations_str = previous_recommendations.raw
                    elif hasattr(previous_recommendations, '__str__'):
                        previous_recommendations_str = str(previous_recommendations)
                    print(f"Converted previous_recommendations object to string: {len(previous_recommendations_str)} characters")
                
                # Source 3: Generate from restaurants list as last resort
                if not previous_recommendations_str or len(previous_recommendations_str.strip()) < 100 or previous_recommendations_str == "None":
                    print("WARNING: Failed to find valid recommendations. Using restaurant list as fallback...")
                    
                    # Try original_restaurants attribute first
                    restaurants_to_use = []
                    if hasattr(self, 'original_restaurants') and self.original_restaurants:
                        restaurants_to_use = self.original_restaurants
                        print(f"Using {len(restaurants_to_use)} restaurants from original_restaurants attribute")
                    elif isinstance(self.state.get("search", {}).get("restaurants", []), list) and len(self.state["search"]["restaurants"]) > 0:
                        restaurants_to_use = self.state["search"]["restaurants"]
                        print(f"Using {len(restaurants_to_use)} restaurants from state.search.restaurants")
                    
                    if restaurants_to_use:
                        location_str = original_location or self.original_location or self.state.get("search", {}).get("location", "your selected location")
                        previous_recommendations_str = f"Recommendations for restaurants in {location_str}:\n\n"
                        for restaurant in restaurants_to_use:
                            name = restaurant.get("name", "Unknown Restaurant")
                            cuisine = restaurant.get("cuisine", "Various")
                            price_range = restaurant.get("priceRange", "$-$$$")
                            rating = restaurant.get("rating", "Not rated")
                            previous_recommendations_str += f"- **{name}**: {cuisine} cuisine, {price_range}, Rating: {rating}\n"
                        print(f"Generated fallback recommendations: {len(previous_recommendations_str)} characters")
        
        # Final validation - if still empty, use placeholder
        if not previous_recommendations_str or len(previous_recommendations_str.strip()) < 100:
            # Emergency fallback: Create generic recommendations for the location
            location_str = original_location or self.original_location or self.state.get("search", {}).get("location", "your selected location")
            previous_recommendations_str = f"Here are some general restaurant recommendations for {location_str}:\n\n"
            previous_recommendations_str += f"1. **Top-rated restaurants in {location_str}** - Various cuisines, $$-$$$\n\n"
            previous_recommendations_str += f"2. **Local favorites in {location_str}** - Regional specialties, $$-$$$\n\n"
            previous_recommendations_str += f"3. **Fine dining experiences in {location_str}** - Upscale cuisine, $$$-$$$$\n\n"
            previous_recommendations_str += f"4. **Hidden gems in {location_str}** - Unique dining experiences, $$\n\n"
            previous_recommendations_str += f"5. **Family-friendly options in {location_str}** - Casual dining, $-$$\n\n"
            
            print(f"WARNING: Created generic recommendations template for {location_str}")
        
        print(f"Final recommendations length: {len(previous_recommendations_str)}")
        print("===== END RECOMMENDATION RETRIEVAL =====\n")
            
        # Log clear context for processing
        print(f"Processing feedback with location: '{original_location}', feedback: '{feedback_text}'")
        print(f"Previous recommendations string length: {len(previous_recommendations_str)}")
        print(f"Previous recommendations preview: {previous_recommendations_str[:100]}...")
        
        # For CopilotKit action compatibility
        self._emit_tool_call("respond_to_feedback", {
            "location": original_location,
            "feedback": feedback_text,
            "previous_recommendations": previous_recommendations_str
        }, "feedback")
            
        # Call the actual task with the CrewAI naming - explicitly mark as recommendation specialist task
        print("*** Using Recommendation Specialist for feedback handling (not Research Specialist) ***")
        
        # For CrewAI task execution
        self._emit_tool_call("respond_to_feedback_task", {
            "location": original_location,
            "feedback": feedback_text,
            "previous_recommendations": previous_recommendations_str
        }, "feedback")
          
        try:
            # Find the respond_to_feedback_task in the crew
            feedback_task = None
            
            # Locate the feedback task
            for task in self.crew.tasks:
                task_str = str(task)
                if 'respond_to_feedback_task' in task_str:
                    feedback_task = task
                    break
            
            if not feedback_task:
                raise ValueError("Feedback task not found in the crew")
            
            # Ensure this task is assigned to the recommendation specialist
            agent_name = str(feedback_task.agent.role)
            if "Recommendation Specialist" in agent_name:
                print(f"✓ Confirmed feedback task is assigned to {agent_name}")
            else:
                print(f"WARNING: Feedback task is assigned to {agent_name}, not Recommendation Specialist")
              # Create input parameters for the feedback task
            feedback_inputs = {
                "location": original_location,
                "feedback": feedback_text,
                "previous_recommendations": previous_recommendations_str
            }
              # CRITICAL FIX: Enhance prompt to explicitly remind the agent to reuse the original list
            if "thank" in feedback_text.lower() or "good" in feedback_text.lower() or "perfect" in feedback_text.lower() or "great" in feedback_text.lower():
                print("User feedback indicates satisfaction. Adding explicit instruction to preserve original recommendations.")
                
                # Instead of setting instructions directly, add it to the input parameters
                feedback_inputs["preservation_instructions"] = f"""
IMPORTANT INSTRUCTION: The user is satisfied with the original recommendations for {original_location}.
You MUST preserve the EXACT same restaurants from the original list with the EXACT same formatting.
DO NOT replace the restaurants with different ones from other cities or locations.
The restaurants should be from {original_location} only, as in the original recommendations.
Simply add a friendly closing message thanking the user and then include the ORIGINAL list.
"""
                print(f"Enhanced task inputs with preservation instructions")
            
            # Create a new Crew instance with just the feedback task
            feedback_crew = Crew(
                agents=[feedback_task.agent],
                tasks=[feedback_task],
                verbose=True
            )
            
            # Execute the crew with just the feedback task
            print("Executing feedback task with enhanced instructions...")
            task_output = await asyncio.to_thread(feedback_crew.kickoff, feedback_inputs)
              # Process task_output to ensure it's usable for the frontend
            result_text = ""
            if hasattr(task_output, 'raw'):
                result_text = task_output.raw
                print(f"Using task_output.raw for recommendations, length: {len(result_text)}")
            elif hasattr(task_output, '__str__'):
                result_text = str(task_output)
                print(f"Using string conversion for recommendations, length: {len(result_text)}")
            else:
                result_text = "No updated recommendations available"
                print("Warning: No proper task_output data available")
            
            print(f"FEEDBACK RESULT PREVIEW: {result_text[:100]}...")

            # Update state with completion
            self._update_state([
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
                },                {
                    "op": "replace",
                    "path": "/processing/recommendations",
                    "value": result_text
                },
                {
                    "op": "replace",
                    "path": "/ui/showFeedbackPrompt",
                    "value": False
                }
            ])
              # Send text message with the result
            result_text = task_output
            if hasattr(task_output, 'raw'):
                result_text = task_output.raw
            if hasattr(task_output, '__str__'):
                result_text = str(task_output)            # CRITICAL FIX: Verify that when the user accepts recommendations, we're keeping the original cities
            # This is a final check to prevent the global restaurant issue
            original_recommendations = self.state.get("processing", {}).get("recommendations", "")
            
            if ("thank" in feedback_text.lower() or "good" in feedback_text.lower() or 
                "perfect" in feedback_text.lower() or "great" in feedback_text.lower() or
                "look" in feedback_text.lower()):
                
                # Get original location
                location = original_location or self.state.get("search", {}).get("location", "")
                location_parts = location.lower().split(',')[0].strip() if location else ""
                
                # Log for debugging
                print(f"VERIFICATION CHECK: Original location='{location}', parsed primary city='{location_parts}'")
                print(f"Original recommendations length: {len(original_recommendations) if original_recommendations else 0}")
                
                # More sophisticated check for mismatched locations 
                mismatched_location = False
                common_cities = [
                    "new york", "copenhagen", "paris", "tokyo", "london", "rome", "bangkok", 
                    "los angeles", "milan", "san francisco", "berlin", "madrid", "sydney", 
                    "dubai", "chicago", "mumbai", "seoul", "nairobi", "amsterdam", "barcelona", 
                    "austin", "seattle", "las vegas", "miami", "boston", "portland", "vancouver", "atlanta"
                ]
                
                # Cache the original recommendations immediately to ensure we have them
                preserved_recommendations = original_recommendations
                
                # ENHANCED VERIFICATION: Better handling of location mismatches
                if location_parts and len(location_parts) > 2:  # Valid location to check against
                    # Check if results mention major cities not in the original location
                    mentioned_cities = []
                    for city in common_cities:
                        if city in result_text.lower() and city not in location_parts.lower():
                            mentioned_cities.append(city)
                    
                    # Detect mismatch if foreign cities are found in the text
                    if mentioned_cities:
                        print(f"WARNING: Detected city mismatch! Found {mentioned_cities} in text but location is '{location}'")
                        mismatched_location = True
                    
                    # Double verification with special markers like "in New York" or "from Copenhagen"
                    city_phrases = [f"in {city}" for city in common_cities] + [f"from {city}" for city in common_cities]
                    for phrase in city_phrases:
                        if phrase.lower() in result_text.lower() and phrase.lower().split()[-1] not in location_parts.lower():
                            print(f"WARNING: Found explicit location phrase '{phrase}' in response text!")
                            mismatched_location = True
                
                # Check if recommendations don't mention the original location at all
                if location_parts and len(location_parts) > 2 and location_parts not in result_text.lower():
                    print(f"WARNING: Original location '{location_parts}' not mentioned in recommendations at all!")
                    mismatched_location = True
                
                if mismatched_location and preserved_recommendations and len(preserved_recommendations) > 100:
                    print("Using original recommendations instead of incorrect global ones")
                    result_text = f"I'm so glad you liked my recommendations for {location}! Here they are again:\n\n{preserved_recommendations}"
                elif len(preserved_recommendations) > 100:
                    print("Using preserved recommendations to ensure consistency")
                    # Prepend a thank you message to the original recommendations
                    result_text = f"Thank you for your feedback! I'm glad you liked the recommendations for {location}. Here they are again:\n\n{preserved_recommendations}"
            
            # Log the successful feedback processing
            print("\n===============================================")
            print("FEEDBACK PROCESSING COMPLETED SUCCESSFULLY")
            print(f"Setting phase to 'feedback_completed'")
            print(f"Setting recommendations with content of length: {len(result_text)}")
            print("===============================================\n")
            
            # Send message following AG-UI protocol
            self._emit_text_message(result_text)
            
            # Return processed result text instead of raw task_output for consistent formatting
            return result_text
            
        except Exception as e:
            print(f"Error processing feedback: {e}")
            self._update_state([
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "error"
                },
                {
                    "op": "replace",
                    "path": "/status/error",
                    "value": str(e)
                }
            ])
            raise e        
    
    # AG-UI protocol state management methods
    def _update_state(self, deltas: List[Dict[str, Any]]):
        """
        Update the state and emit a state delta event
        
        Args:
            deltas: List of JSON Patch operations
        """
        # Check if state exists, and initialize it if not
        if not self.state or not isinstance(self.state, dict):
            print("Warning: Reinitializing empty state before applying updates")
            self.state = {
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
                    "feedbackOptions": []
                }
            }
            
        # Log important state changes like phase transitions
        for delta in deltas:
            if delta.get("path") == "/status/phase":
                print(f"\n==== STATE PHASE CHANGE: '{delta.get('value')}' ====\n")
                
        # Actually apply patches to internal state
        filtered_deltas = []
        for delta in deltas:
            try:
                path_parts = delta["path"].strip("/").split("/")
                current = self.state
                  # Navigate to the parent object, creating nested objects if they don't exist
                for i in range(len(path_parts) - 1):
                    part = path_parts[i]
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Apply the operation based on type
                op = delta.get("op", "replace")  # Default to replace
                last_key = path_parts[-1]
                
                if op == "replace":
                    current[last_key] = delta["value"]
                    filtered_deltas.append(delta)
                elif op == "add":
                    if isinstance(current, list):
                        current.append(delta["value"])
                    else:
                        current[last_key] = delta["value"]
                    filtered_deltas.append(delta)
                elif op == "remove":
                    if last_key in current:
                        del current[last_key]
                        filtered_deltas.append(delta)
            except Exception as e:
                print(f"Failed to apply state update: {str(e)}, delta: {delta}")        # Emit state delta event if callback is provided and we have valid deltas
        if self.event_callback and filtered_deltas:
            # Check if this contains any important phase changes
            important_phase_changes = [d for d in filtered_deltas if d.get("path") == "/status/phase"]
            if important_phase_changes:
                for phase_change in important_phase_changes:
                    current_phase = phase_change.get("value")
                    print(f"EMITTING IMPORTANT PHASE CHANGE: {current_phase}")
                
                # Add explicit progress update for visibility of phase
                if any(d.get("value") == "restaurants_found" for d in important_phase_changes):
                    print("Adding explicit progress update for restaurants_found phase")
                    filtered_deltas.append({
                        "op": "replace",
                        "path": "/processing/progress",
                        "value": 0.5
                    })
                elif any(d.get("value") == "presenting_recommendations" for d in important_phase_changes):
                    print("Adding explicit progress update for presenting_recommendations phase")
                    filtered_deltas.append({
                        "op": "replace",
                        "path": "/processing/progress",
                        "value": 0.7
                    })
            
            # Emit the state delta event
            self.event_callback({
                "type": "STATE_DELTA",
                "message_id": self.message_id,
                "delta": filtered_deltas
            })
    # AG-UI protocol event emission methods
    def _emit_tool_call(self, tool_name: str, args: Dict[str, Any], task_type: str = None):
        """
        Emit tool call events with task tracking
        
        Args:
            tool_name: Name of the tool/task
            args: Tool/task arguments
            task_type: The type of task (search, recommend, feedback)
        """
        if not self.event_callback:
            return
        
        # If this is a search-related tool call, ensure location is properly extracted
        if "search" in tool_name.lower() and "location" in args:
            location = args.get("location", "")
            print(f"Checking location parameter: '{location}'")
            
            # If location looks like JSON, try to extract actual location
            if isinstance(location, str) and location and (location.startswith('{') and location.endswith('}')):
                try:
                    import json
                    location_data = json.loads(location)
                    if isinstance(location_data, dict):
                        if "originalLocation" in location_data:
                            args["location"] = location_data["originalLocation"]
                            print(f"Extracted location from JSON parameter: '{args['location']}'")
                        elif "feedbackText" in location_data and "originalLocation" in location_data:
                            args["location"] = location_data["originalLocation"]
                            print(f"Extracted location from feedback JSON: '{args['location']}'")
                except (json.JSONDecodeError, TypeError):
                    # Not valid JSON, keep as is
                    print(f"Location parameter appears to be JSON but could not be parsed: '{location}'")
        
        # Debug log
        print(f"EMITTING TOOL CALL: {tool_name} with args: {args} (task_type: {task_type})")
        
        # Generate a tool call ID
        tool_call_id = f"call_{str(uuid.uuid4())[:8]}"
        
        # Map task names to types if not provided
        if task_type is None:
            if "search" in tool_name.lower():
                task_type = "search"
            elif "recommend" in tool_name.lower() or "present" in tool_name.lower():
                task_type = "recommend"
            elif "feedback" in tool_name.lower() or "respond" in tool_name.lower():
                task_type = "feedback"
        
        # Update current phase in state based on task type
        if task_type:
            self._update_state([{
                "op": "replace",
                "path": "/processing/currentPhase",
                "value": task_type
            }])
        
        # Format display name for the tool call
        display_name = tool_name
        if task_type:
            task_type_display = {
                "search": "Restaurant Search",
                "recommend": "Recommendation Generation",
                "feedback": "Feedback Processing"
            }.get(task_type, task_type.capitalize())
            display_name = f"{task_type_display} Task"
            
        # Tool call start
        self.event_callback({
            "type": "TOOL_CALL_START",
            "message_id": self.message_id,
            "toolCallId": tool_call_id,
            "toolCallName": display_name,
            "tool": tool_name
        })
        
        # Tool call args
        self.event_callback({
            "type": "TOOL_CALL_ARGS",
            "message_id": self.message_id,
            "toolCallId": tool_call_id,
            "toolCallName": tool_name,
            "args": args
        })
        
        # Tool call end
        self.event_callback({
            "type": "TOOL_CALL_END",
            "message_id": self.message_id,
            "toolCallId": tool_call_id,
            "toolCallName": tool_name
        })
    
    def _emit_text_message(self, content: str):
        """
        Emit text message events following AG-UI protocol
        
        Args:
            content: The text content to send
        """
        if not self.event_callback:
            return
        
        # Text message start event
        self.event_callback({
            "type": "TEXT_MESSAGE_START",
            "message_id": self.message_id,
            "role": "assistant"
        })
        
        # Text message content event
        self.event_callback({
            "type": "TEXT_MESSAGE_CONTENT",
            "message_id": self.message_id,
            "delta": content  # Important: delta must be a string
        })
        
        # Text message end event
        self.event_callback({
            "type": "TEXT_MESSAGE_END",
            "message_id": self.message_id,
            "delta": ""  # Important: delta must be a string, even if empty
        })
    
    def _parse_restaurants(self, result) -> List[Dict[str, Any]]:
        """
        Parse restaurant information from the CrewAI result
        
        Args:
            result: The result from CrewAI (could be string or CrewOutput)
            
        Returns:
            List of restaurant objects
        """
        restaurants = []
        
        # Convert CrewOutput to string if needed
        result_text = ""
        if hasattr(result, 'raw'):
            # It's a CrewOutput object
            result_text = result.raw
        elif hasattr(result, '__str__'):
            # It can be converted to string
            result_text = str(result)
        else:
            # Fallback
            result_text = "No results available"
        
        try:
            # Example parsing - modify based on your actual result structure
            lines = result_text.split('\n')
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
