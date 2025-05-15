"use client";

import React, { useRef } from "react";
import {
  useCoAgent,
  useCoAgentStateRender,
  useCopilotAction,
} from "@copilotkit/react-core";
import { Restaurant, RestaurantFinderAgentState } from "@/lib/restaurant-types";
import Image from "next/image";
import ReactMarkdown from "react-markdown";

/**
 * RestaurantFinder Component
 * Connects to the restaurant finder agent via CopilotKit and displays UI for restaurant search
 */
function RestaurantFinder() {
  // Reference to track if restaurant finding is in progress
  const isProcessingInProgress = useRef(false);

  // Connect to the agent's state using CopilotKit's useCoAgent hook
  const {
    state,
    stop: stopRestaurantAgent,
    setState,
  } = useCoAgent<RestaurantFinderAgentState>({
    name: "restaurantFinderAgent",
    initialState: {
      status: { phase: "idle", error: null },
      search: {
        query: "",
        location: "",
        stage: "not_started",
        restaurants_found: 0,
        restaurants: [],
        completed: false,
      },
      processing: {
        progress: 0,
        recommendations: null,
        completed: false,
        inProgress: false,
        currentPhase: "",
        phases: ["search", "recommend", "feedback"],
      },
      ui: {
        showRestaurants: false,
        showProgress: false,
        activeTab: "chat",
        showFeedbackPrompt: false,
        feedbackOptions: [
          "Thanks for the recommendations! These look perfect.",
          "Can you suggest more restaurants with different cuisines?",
          "I'm looking for more budget-friendly dining options.",
          "I prefer upscale fine dining experiences. Any suggestions?",
          "Are there any restaurants with unique dining experiences?",
        ],
      },
    },
  });

  // Helper function for type-safe phase comparison
  const isPhase = (
    phase: string | undefined,
    comparePhase: RestaurantFinderAgentState["status"]["phase"]
  ): boolean => {
    return phase === comparePhase;
  };

  // Add a state change logger to debug feedback issues
  React.useEffect(() => {
    if (state?.status?.phase === "await_feedback") {
      console.log("State changed to await_feedback:", {
        phase: state.status.phase,
        showFeedbackPrompt: state.ui?.showFeedbackPrompt,
        feedbackOptions: state.ui?.feedbackOptions,
      });
    }
  }, [
    state?.status?.phase,
    state?.ui?.showFeedbackPrompt,
    state?.ui?.feedbackOptions,
  ]);
  // Add general state phase change logger
  React.useEffect(() => {
    if (state?.status?.phase) {
      console.log(`State phase changed to: ${state.status.phase}`, {
        timestamp: new Date().toISOString(),
        phase: state.status.phase,
        processingProgress: state?.processing?.progress,
        processingInProgress: state?.processing?.inProgress,
        currentProcessingPhase: state?.processing?.currentPhase,
      }); // Reset isProcessingInProgress only when feedback is fully completed
      if (state.status.phase === "feedback_completed") {
        console.log(
          "Resetting isProcessingInProgress to false due to completed state"
        );
        isProcessingInProgress.current = false;
      }
    }
  }, [
    state?.processing?.currentPhase,
    state?.processing?.inProgress,
    state?.processing?.progress,
    state.status.phase,
  ]);

  // Implement useCoAgentStateRender hook for real-time UI updates
  useCoAgentStateRender({
    name: "restaurantFinderAgent",
    handler: ({ nodeName }) => {
      // Stop the agent when the "__end__" node is reached
      if (nodeName === "__end__") {
        setTimeout(() => {
          isProcessingInProgress.current = false;
          stopRestaurantAgent();
        }, 1000);
      }
    },
    render: ({ status }) => {
      if (status === "inProgress") {
        isProcessingInProgress.current = true;
        return (
          <div className="restaurant-search-in-progress bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center gap-2 mb-3">
              <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span className="font-medium">{getStatusText()}</span>
            </div>

            <div className="status-container mb-3">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                  style={{
                    width: `${(state?.processing?.progress || 0) * 100}%`,
                  }}></div>
              </div>
            </div>

            {state?.search?.restaurants_found > 0 && (
              <div className="text-xs text-gray-500 flex items-center gap-1.5">
                <span className="text-blue-500">&#x1F50E;</span>
                Found {state.search.restaurants_found} restaurant
                {state.search.restaurants_found !== 1 ? "s" : ""}
              </div>
            )}
          </div>
        );
      }

      // When processing is complete, don't return any UI from this render function
      // The main component will handle showing results
      if (status === "complete") {
        isProcessingInProgress.current = false;
        return null;
      }

      return null;
    },
  });

  // Implement useCopilotAction for human-in-the-loop feedback
  useCopilotAction({
    name: "provideFeedback",
    description:
      "Allow the user to provide feedback on restaurant recommendations",
    parameters: [
      {
        name: "feedbackOptions",
        type: "string[]",
        description: "List of feedback options for the user to choose from",
        required: true,
      },
      {
        name: "message",
        type: "string",
        description:
          "A message to display to the user when asking for feedback",
        required: true,
      },
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      console.log("provideFeedback action called with full args:", args);

      // Parse the args - no need to check for nested args
      let feedbackOptions = args?.feedbackOptions;
      let message = args?.message;

      console.log("Extracted values:", {
        feedbackOptions,
        message,
        respondIsAvailable: !!respond,
      }); // Default values if none provided
      if (!Array.isArray(feedbackOptions)) {
        feedbackOptions = [
          "Thank you for the recommendations! These look perfect.",
          "Can you suggest more restaurants with different cuisines?",
          "I'm looking for more budget-friendly dining options.",
          "I prefer upscale fine dining experiences. Any suggestions?",
          "Are there any restaurants with unique dining experiences?",
        ];
      }

      if (!message) {
        message = "How do you feel about these recommendations?";
      }

      if (!respond) {
        return <div>Loading feedback options...</div>;
      }
      return (
        <div className="feedback-section mt-6 pt-4 border-t border-gray-200">
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-blue-500 text-xl">💬</span>
              <span className="font-medium text-blue-600">
                Restaurant Recommendation Specialist
              </span>
            </div>
            <h3 className="text-lg font-medium mb-2">
              {message || "How do you feel about these recommendations?"}
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {feedbackOptions.map((option, index) => (
              <button
                key={index}
                className="px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-800 rounded-full text-sm border border-gray-200 transition-colors"
                onClick={() => {
                  // Update UI state to show processing
                  setState(() => {
                    return {
                      ...state,
                      processing: {
                        ...state.processing,
                        inProgress: true,
                      },
                      status: {
                        ...state.status,
                        phase: "processing_feedback",
                      },
                    };
                  });

                  // Get the original location from state
                  const originalLocation = state?.search?.location || "";

                  // Create a properly structured feedback object
                  const feedbackObject = {
                    feedbackText: option,
                    originalLocation: originalLocation,
                  };

                  // Convert the object to a JSON string
                  const feedbackJsonString = JSON.stringify(feedbackObject);

                  console.log(`Sending feedback: ${feedbackJsonString}`);

                  // Send the JSON string - backend will parse this
                  respond(feedbackJsonString);
                }}>
                {option}
              </button>
            ))}
          </div>
        </div>
      );
    },
  });

  // Helper function to format the status for display
  const getStatusText = () => {
    // First check the main phase
    switch (state?.status?.phase) {
      case "initialized":
        return "Ready to search for restaurants";
      case "searching_restaurants":
        return "Searching for restaurants...";
      case "restaurants_found":
        return "Found restaurants, preparing recommendations...";
      case "presenting_recommendations":
        return "Creating personalized recommendations...";
      case "await_feedback":
        return "Ready for your feedback";
      case "processing_feedback":
        return "Processing your feedback...";
      case "completed":
        return "Restaurant recommendations ready";
      case "feedback_completed":
        return "Updated recommendations based on your feedback";
      default:
        return "Ready to assist";
    }
  }; // Display restaurant processing progress UI
  if (
    state?.status &&
    state.status.phase !== "completed" &&
    state.status.phase !== "feedback_completed" &&
    (isProcessingInProgress.current ||
      state?.processing?.inProgress ||
      state.status.phase === "await_feedback")
  ) {
    return (
      <div className="flex flex-col gap-4 h-full max-w-4xl mx-auto">
        <div className="p-6 bg-white border rounded-lg shadow-sm w-full">
          <h3 className="text-xl font-semibold mb-4">Finding Restaurants</h3>

          <div className="status-container mb-6">
            <p className="text-gray-700 mb-2">{getStatusText()}</p>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                style={{
                  width: `${(state?.processing?.progress || 0) * 100}%`,
                }}></div>
            </div>
          </div>

          <div className="restaurant-stages my-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              Search Process
            </h4>
            <div className="stages-container flex flex-col gap-2">
              {/* Research Phase */}{" "}
              <div
                className={`stage-item p-3 rounded-md border ${
                  isPhase(state?.status?.phase, "searching_restaurants")
                    ? "border-blue-400 bg-blue-50"
                    : isPhase(state?.status?.phase, "restaurants_found") ||
                      isPhase(
                        state?.status?.phase,
                        "presenting_recommendations"
                      ) ||
                      isPhase(state?.status?.phase, "await_feedback") ||
                      isPhase(state?.status?.phase, "processing_feedback") ||
                      isPhase(state?.status?.phase, "completed") ||
                      isPhase(state?.status?.phase, "feedback_completed")
                    ? "border-green-400 bg-green-50"
                    : "border-gray-200"
                }`}>
                <div className="flex items-center gap-2">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                      isPhase(state?.status?.phase, "searching_restaurants")
                        ? "bg-blue-500 text-white"
                        : isPhase(state?.status?.phase, "restaurants_found") ||
                          isPhase(
                            state?.status?.phase,
                            "presenting_recommendations"
                          ) ||
                          isPhase(state?.status?.phase, "await_feedback") ||
                          isPhase(
                            state?.status?.phase,
                            "processing_feedback"
                          ) ||
                          isPhase(state?.status?.phase, "completed") ||
                          isPhase(state?.status?.phase, "feedback_completed")
                        ? "bg-green-500 text-white"
                        : "bg-gray-200"
                    }`}>
                    {" "}
                    {isPhase(state?.status?.phase, "restaurants_found") ||
                    isPhase(
                      state?.status?.phase,
                      "presenting_recommendations"
                    ) ||
                    isPhase(state?.status?.phase, "await_feedback") ||
                    isPhase(state?.status?.phase, "processing_feedback") ||
                    isPhase(state?.status?.phase, "completed") ||
                    isPhase(state?.status?.phase, "feedback_completed")
                      ? "✓"
                      : "1"}
                  </span>
                  <span className="font-medium text-sm">
                    Finding Restaurants
                  </span>
                </div>
                {isPhase(state?.status?.phase, "searching_restaurants") && (
                  <p className="text-xs text-gray-600 mt-1 ml-7">
                    Searching for restaurants in{" "}
                    {state?.search?.location || "your location"}
                  </p>
                )}
              </div>
              {/* Recommendations Phase */}{" "}
              <div
                className={`stage-item p-3 rounded-md border ${
                  isPhase(state?.status?.phase, "presenting_recommendations")
                    ? "border-blue-400 bg-blue-50"
                    : isPhase(state?.status?.phase, "await_feedback") ||
                      isPhase(state?.status?.phase, "processing_feedback") ||
                      isPhase(state?.status?.phase, "completed") ||
                      isPhase(state?.status?.phase, "feedback_completed")
                    ? "border-green-400 bg-green-50"
                    : "border-gray-200"
                }`}>
                <div className="flex items-center gap-2">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                      isPhase(
                        state?.status?.phase,
                        "presenting_recommendations"
                      )
                        ? "bg-blue-500 text-white"
                        : isPhase(state?.status?.phase, "await_feedback") ||
                          isPhase(
                            state?.status?.phase,
                            "processing_feedback"
                          ) ||
                          isPhase(state?.status?.phase, "completed") ||
                          isPhase(state?.status?.phase, "feedback_completed")
                        ? "bg-green-500 text-white"
                        : "bg-gray-200"
                    }`}>
                    {" "}
                    {isPhase(state?.status?.phase, "await_feedback") ||
                    isPhase(state?.status?.phase, "processing_feedback") ||
                    isPhase(state?.status?.phase, "completed") ||
                    isPhase(state?.status?.phase, "feedback_completed")
                      ? "✓"
                      : "2"}
                  </span>
                  <span className="font-medium text-sm">
                    Creating Recommendations
                  </span>
                </div>
                {isPhase(
                  state?.status?.phase,
                  "presenting_recommendations"
                ) && (
                  <p className="text-xs text-gray-600 mt-1 ml-7">
                    Analyzing restaurant options
                  </p>
                )}
              </div>
              {/* Feedback Phase */}
              <div
                className={`stage-item p-3 rounded-md border ${
                  isPhase(state?.status?.phase, "await_feedback") ||
                  isPhase(state?.status?.phase, "processing_feedback")
                    ? "border-blue-400 bg-blue-50"
                    : isPhase(state?.status?.phase, "completed") ||
                      isPhase(state?.status?.phase, "feedback_completed")
                    ? "border-green-400 bg-green-50"
                    : "border-gray-200"
                }`}>
                <div className="flex items-center gap-2">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                      isPhase(state?.status?.phase, "await_feedback") ||
                      isPhase(state?.status?.phase, "processing_feedback")
                        ? "bg-blue-500 text-white"
                        : isPhase(state?.status?.phase, "completed") ||
                          isPhase(state?.status?.phase, "feedback_completed")
                        ? "bg-green-500 text-white"
                        : "bg-gray-200"
                    }`}>
                    {isPhase(state?.status?.phase, "completed") ||
                    isPhase(state?.status?.phase, "feedback_completed")
                      ? "✓"
                      : "3"}
                  </span>
                  <span className="font-medium text-sm">
                    Feedback & Refinement
                  </span>
                </div>
                {(isPhase(state?.status?.phase, "await_feedback") ||
                  isPhase(state?.status?.phase, "processing_feedback")) && (
                  <p className="text-xs text-gray-600 mt-1 ml-7">
                    Waiting for your feedback
                  </p>
                )}
              </div>
            </div>
          </div>

          {state?.search?.restaurants_found > 0 && (
            <div className="mt-4 text-sm text-gray-600">
              <p>
                Found {state.search.restaurants_found} restaurants matching your
                criteria
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // When recommendations are ready, display them
  if (
    state?.status?.phase === "completed" ||
    state?.status?.phase === "feedback_completed"
  ) {
    // Debug logging
    console.log("Recommendations render state:", {
      phase: state?.status?.phase,
      hasFeedback: !!state?.processing?.feedback,
      feedbackText: state?.processing?.feedback || "none",
      hasRecommendations: !!state?.processing?.recommendations,
      recommendationsLength: state?.processing?.recommendations?.length || 0,
    });

    // Ensure processing state is reset when recommendations are ready to display
    if (state?.status?.phase === "feedback_completed") {
      // Make sure processing state is reset
      isProcessingInProgress.current = false;
    }

    // Determine if this is after feedback processing
    const isFeedbackProcessed = state?.status?.phase === "feedback_completed";

    return (
      <div className="flex flex-col gap-4 h-full max-w-4xl mx-auto">
        <div className="p-6 bg-white border rounded-lg shadow-sm w-full">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              {isFeedbackProcessed
                ? "Updated Recommendations"
                : "Restaurant Recommendations"}
            </h2>
            {state?.search?.location && (
              <div className="text-sm px-3 py-1.5 bg-blue-50 text-blue-800 border border-blue-100 rounded-md">
                Location:{" "}
                <span className="font-medium">{state.search.location}</span>
              </div>
            )}
          </div>{" "}
          {/* Show feedback response message if present */}
          {isFeedbackProcessed && state?.processing?.feedback && (
            <div className="mb-4 p-3 bg-green-50 border border-green-100 rounded-md text-green-700">
              <p className="text-sm font-medium">
                Based on your feedback: &ldquo;{state.processing.feedback}
                &rdquo;
              </p>
            </div>
          )}{" "}
          {/* Render recommendations */}
          <div className="prose prose-slate max-w-none">
            {state?.processing?.recommendations && (
              <div className="recommendations-content prose prose-slate max-w-none prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:my-2 prose-a:text-blue-600 hover:prose-a:underline prose-li:my-1">
                {" "}
                <ReactMarkdown
                  components={{
                    h1: ({ ...props }) => (
                      <h1 className="text-2xl font-bold mt-6 mb-3" {...props} />
                    ),
                    h2: ({ ...props }) => (
                      <h2
                        className="text-xl font-bold mt-5 mb-2 text-blue-700"
                        {...props}
                      />
                    ),
                    h3: ({ ...props }) => (
                      <h3
                        className="text-lg font-semibold mt-4 mb-2"
                        {...props}
                      />
                    ),
                    h4: ({ ...props }) => (
                      <h4
                        className="text-base font-semibold mt-3 mb-2"
                        {...props}
                      />
                    ),
                    strong: ({ children, ...props }) => {
                      // Check if the text looks like a restaurant name or rating
                      const text = String(children);
                      if (text.includes("★") || /\d(\.\d)?\/5/.test(text)) {
                        // Highlight ratings
                        return (
                          <strong
                            className="font-medium text-amber-500"
                            {...props}>
                            {children}
                          </strong>
                        );
                      } else if (
                        /^[A-Z][\w\s'&,-]+$/.test(text) &&
                        text.length > 3
                      ) {
                        // Highlight restaurant names
                        return (
                          <strong
                            className="font-semibold text-blue-700"
                            {...props}>
                            {children}
                          </strong>
                        );
                      }
                      return (
                        <strong className="font-semibold" {...props}>
                          {children}
                        </strong>
                      );
                    },
                    a: ({ href, ...props }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                        {...props}
                      />
                    ),
                    ul: ({ ...props }) => (
                      <ul className="list-disc pl-6 my-3" {...props} />
                    ),
                    ol: ({ ...props }) => (
                      <ol className="list-decimal pl-6 my-3" {...props} />
                    ),
                    li: ({ ...props }) => <li className="mb-1" {...props} />,
                    p: ({ ...props }) => <p className="my-2" {...props} />,
                    blockquote: ({ ...props }) => (
                      <blockquote
                        className="pl-4 border-l-4 border-gray-200 text-gray-700 italic my-4"
                        {...props}
                      />
                    ),
                    code: ({ ...props }) => (
                      <code
                        className="bg-gray-100 px-1 py-0.5 rounded text-sm"
                        {...props}
                      />
                    ),
                    pre: ({ ...props }) => (
                      <pre
                        className="bg-gray-100 p-3 rounded overflow-x-auto my-4"
                        {...props}
                      />
                    ),
                    table: ({ ...props }) => (
                      <table
                        className="border-collapse border border-gray-300 my-4 w-full"
                        {...props}
                      />
                    ),
                    thead: ({ ...props }) => (
                      <thead className="bg-gray-100" {...props} />
                    ),
                    tbody: ({ ...props }) => <tbody {...props} />,
                    tr: ({ ...props }) => (
                      <tr className="border-b border-gray-300" {...props} />
                    ),
                    th: ({ ...props }) => (
                      <th
                        className="border border-gray-300 px-3 py-2 text-left"
                        {...props}
                      />
                    ),
                    td: ({ ...props }) => (
                      <td
                        className="border border-gray-300 px-3 py-2"
                        {...props}
                      />
                    ),
                    img: ({ src, alt, ...props }) => (
                      <img
                        src={src}
                        alt={alt || "Restaurant image"}
                        className="rounded-md my-4 max-w-full h-auto"
                        {...props}
                      />
                    ),
                  }}>
                  {state.processing.recommendations}
                </ReactMarkdown>
              </div>
            )}
          </div>
          {/* Display restaurant list when available */}
          {state?.search?.restaurants &&
            state.search.restaurants.length > 0 &&
            state?.ui?.showRestaurants && (
              <div className="restaurants-grid mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
                {state.search.restaurants.map((restaurant: Restaurant) => (
                  <div
                    key={restaurant.id}
                    className="restaurant-card border rounded-md p-4 hover:shadow-md transition-shadow">
                    {restaurant.imageUrl && (
                      <div className="restaurant-image mb-3 h-40 w-full relative rounded-md overflow-hidden">
                        <Image
                          src={restaurant.imageUrl}
                          alt={restaurant.name}
                          fill
                          className="object-cover"
                        />
                      </div>
                    )}
                    <h3 className="font-semibold text-lg">{restaurant.name}</h3>
                    {restaurant.cuisine && (
                      <p className="text-sm text-gray-600">
                        {restaurant.cuisine}
                      </p>
                    )}
                    {restaurant.rating && (
                      <div className="flex items-center gap-1 mt-1">
                        <span className="text-yellow-500">★</span>
                        <span className="text-sm font-medium">
                          {restaurant.rating}
                        </span>
                      </div>
                    )}
                    {restaurant.priceRange && (
                      <p className="text-sm text-gray-700 mt-1">
                        {restaurant.priceRange}
                      </p>
                    )}
                    {restaurant.address && (
                      <p className="text-sm text-gray-500 mt-1">
                        {restaurant.address}
                      </p>
                    )}
                    {restaurant.url && (
                      <a
                        href={restaurant.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block mt-2 text-blue-600 text-sm hover:underline">
                        View Website
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
        </div>
      </div>
    );
  }

  // Default state when not searching and no results yet
  return (
    <div className="flex flex-col gap-4 h-full max-w-4xl mx-auto">
      <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200 w-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Restaurant Finder</h2>
          <span className="px-3 py-1 bg-green-50 text-green-800 text-xs rounded-full border border-green-100">
            Ready
          </span>
        </div>

        <div className="text-gray-600 mb-4">
          <p>
            I can help you find restaurants in any location. Just ask me
            something like:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1 text-gray-500">
            <li>Find Italian restaurants in Chicago</li>
            <li>What are the best sushi places in San Francisco?</li>
            <li>Show me family-friendly restaurants in Boston</li>
          </ul>
        </div>

        <div className="mt-6 p-4 bg-blue-50 border border-blue-100 rounded-md">
          <div className="flex items-center gap-2 text-blue-700">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span className="text-sm font-medium">
              Ask me about restaurants using the chat!
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RestaurantFinder;
