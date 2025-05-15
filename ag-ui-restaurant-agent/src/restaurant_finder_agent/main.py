#!/usr/bin/env python
import sys
from dotenv import load_dotenv
import os

from restaurant_finder_agent.crew import RestaurantFinderTemplateCrew

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding necessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

load_dotenv()  # Add this at the top of your file

def run():
    """
    Run the crew.
    """
    inputs = {
        "location": "San Francisco, CA",
    }

    RestaurantFinderTemplateCrew().run(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {"location": "New York, NY"}
    try:
        RestaurantFinderTemplateCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        RestaurantFinderTemplateCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {"location": "Chicago, IL"}
    try:
        RestaurantFinderTemplateCrew().crew().test(
            n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def start_api():
    """
    Start the AG-UI API server.
    """
    from restaurant_finder_agent.api import start_server
    start_server()
