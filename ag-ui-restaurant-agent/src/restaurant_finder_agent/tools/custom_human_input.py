"""
Custom human input handler for CrewAI
This module provides a custom human input handler that logs when human input is requested
"""

import sys
import time
from datetime import datetime
from typing import List, Optional, Callable


def custom_human_input_handler(
    prompt: str,
    agent_name: Optional[str] = None,
    agent_role: Optional[str] = None,
    task_description: Optional[str] = None,
    previous_responses: Optional[List[str]] = None,
    input_fn: Callable = input,
) -> str:
    """
    Custom human input handler function for CrewAI that logs when human input is requested
    
    Args:
        prompt: The prompt text to show to the human
        agent_name: The name of the agent requesting input
        agent_role: The role of the agent requesting input
        task_description: The description of the task
        previous_responses: Previous human responses
        input_fn: Function to use for getting input (defaults to input())
        
    Returns:
        The human's input as a string
    """
    # Print a clear separator to make the human input request stand out
    print("\n" + "=" * 80)
    print(f"⚠️  HUMAN INPUT REQUESTED AT {datetime.now().strftime('%H:%M:%S')} ⚠️")
    print("=" * 80)
    
    # Print agent information if available
    if agent_role:
        print(f"🤖 AGENT ROLE: {agent_role}")
    if agent_name:
        print(f"🤖 AGENT NAME: {agent_name}")
    if task_description:
        print(f"📋 TASK: {task_description}")
    
    print("\n📝 PROMPT FOR HUMAN:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    # Log where in the code execution is blocked
    print("\n⏳ EXECUTION IS NOW BLOCKED WAITING FOR HUMAN INPUT")
    print("⏳ UI STATE MAY NOT UPDATE UNTIL INPUT IS PROVIDED")
    print("⏳ ALL STATE CHANGES PRIOR TO THIS POINT HAVE BEEN APPLIED")
    
    # Get the human's input
    try:
        print("\n✍️  YOUR RESPONSE (press Enter after typing):")
        response = input_fn()
        print("\n✅ HUMAN INPUT RECEIVED, CONTINUING EXECUTION...")
        print("=" * 80 + "\n")
        return response
    except KeyboardInterrupt:
        print("\n\n❌ Human input interrupted with keyboard interrupt")
        print("⚠️  Returning empty string as response")
        return ""
    except Exception as e:
        print(f"\n\n❌ Error getting human input: {str(e)}")
        print("⚠️  Returning empty string as response")
        return ""
