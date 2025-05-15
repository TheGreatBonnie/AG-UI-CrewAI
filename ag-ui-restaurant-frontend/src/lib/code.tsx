/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useRef } from "react";
import { useCoAgent, useCoAgentStateRender } from "@copilotkit/react-core";
import { RestaurantFinderAgentState, Restaurant } from "@/lib/restaurant-types";
import ReactMarkdown from "react-markdown";

// Restaurant card component to display restaurant information
const RestaurantCard = ({ restaurant }: { restaurant: Restaurant }) => {
  return (
    <div className="restaurant-card p-4 border border-gray-200 rounded-md hover:shadow-md transition-all bg-white">
      <h4 className="text-lg font-medium text-blue-700 mb-2">
        {restaurant.name}
      </h4>
      {restaurant.cuisine && (
        <div className="text-sm mb-1">
          <span className="font-medium">Cuisine:</span> {restaurant.cuisine}
        </div>
      )}
      {restaurant.priceRange && (
        <div className="text-sm mb-1">
          <span className="font-medium">Price:</span> {restaurant.priceRange}
        </div>
      )}
      {restaurant.rating && (
        <div className="text-sm mb-1">
          <span className="font-medium">Rating:</span> {restaurant.rating}
        </div>
      )}
      {restaurant.address && (
        <div className="text-sm mb-1">
          <span className="font-medium">Address:</span> {restaurant.address}
        </div>
      )}
      {restaurant.url && (
        <a
          href={restaurant.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:underline mt-2 inline-block">
          View website
        </a>
      )}
    </div>
  );
};

// Restaurant process stages display component
const RestaurantProcessStages = ({
  state,
}: {
  state: RestaurantFinderAgentState | undefined;
}) => {
  // Helper function for type-safe phase comparison
  const isPhase = (
    phase: string | undefined,
    comparePhase: RestaurantFinderAgentState["status"]["phase"]
  ): boolean => {
    return phase === comparePhase;
  };

  return (
    <div className="process-stages my-4">
      {" "}
      <h4 className="text-sm font-medium text-gray-700 mb-3">
        Two-Phase Workflow
      </h4>
      <div className="stages-container flex flex-col gap-2">
        {" "}
        {/* Research Phase */}
        <div
          className={`stage-item p-3 rounded-md border ${
            isPhase(state?.status?.phase, "research_phase") ||
            isPhase(state?.status?.phase, "searching_restaurants")
              ? "border-blue-400 bg-blue-50"
              : isPhase(state?.status?.phase, "restaurants_found") ||
                isPhase(state?.status?.phase, "recommendation_phase") ||
                isPhase(state?.status?.phase, "generating_recommendations") ||
                isPhase(state?.status?.phase, "completed")
              ? "border-green-400 bg-green-50"
              : "border-gray-200"
          }`}>
          {" "}
          <div className="flex items-center gap-2">
            {" "}
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                isPhase(state?.status?.phase, "research_phase") ||
                isPhase(state?.status?.phase, "searching_restaurants")
                  ? "bg-blue-500 text-white"
                  : isPhase(state?.status?.phase, "restaurants_found") ||
                    isPhase(state?.status?.phase, "recommendation_phase") ||
                    isPhase(
                      state?.status?.phase,
                      "generating_recommendations"
                    ) ||
                    isPhase(state?.status?.phase, "completed")
                  ? "bg-green-500 text-white"
                  : "bg-gray-200"
              }`}>
              {" "}
              {isPhase(state?.status?.phase, "restaurants_found") ||
              isPhase(state?.status?.phase, "recommendation_phase") ||
              isPhase(state?.status?.phase, "generating_recommendations") ||
              isPhase(state?.status?.phase, "completed")
                ? "✓"
                : "1"}
            </span>
            <span className="font-medium text-sm">
              Research Phase: Find Restaurants
            </span>
          </div>{" "}
          {(isPhase(state?.status?.phase, "research_phase") ||
            isPhase(state?.status?.phase, "searching_restaurants")) && (
            <p className="text-xs text-gray-600 mt-1 ml-7">
              The Restaurant Research Specialist is searching in{" "}
              {state?.search?.location}
            </p>
          )}
        </div>{" "}
        {/* Recommendation Phase */}
        <div
          className={`stage-item p-3 rounded-md border ${
            isPhase(state?.status?.phase, "recommendation_phase") ||
            isPhase(state?.status?.phase, "generating_recommendations")
              ? "border-blue-400 bg-blue-50"
              : isPhase(state?.status?.phase, "await_feedback") ||
                isPhase(state?.status?.phase, "processing_feedback") ||
                isPhase(state?.status?.phase, "completed")
              ? "border-green-400 bg-green-50"
              : "border-gray-200"
          }`}>
          <div className="flex items-center gap-2">
            {" "}
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                isPhase(state?.status?.phase, "recommendation_phase") ||
                isPhase(state?.status?.phase, "generating_recommendations")
                  ? "bg-blue-500 text-white"
                  : isPhase(state?.status?.phase, "await_feedback") ||
                    isPhase(state?.status?.phase, "processing_feedback") ||
                    isPhase(state?.status?.phase, "completed")
                  ? "bg-green-500 text-white"
                  : "bg-gray-200"
              }`}>
              {isPhase(state?.status?.phase, "await_feedback") ||
              isPhase(state?.status?.phase, "processing_feedback") ||
              isPhase(state?.status?.phase, "completed")
                ? "✓"
                : "2"}
            </span>
            <span className="font-medium text-sm">Recommendation Phase</span>
          </div>{" "}
          {(isPhase(state?.status?.phase, "recommendation_phase") ||
            isPhase(state?.status?.phase, "generating_recommendations")) && (
            <p className="text-xs text-gray-600 mt-1 ml-7">
              The Restaurant Recommendation Specialist is creating suggestions
            </p>
          )}
        </div>{" "}
        {/* Feedback Phase */}
        <div
          className={`stage-item p-3 rounded-md border ${
            isPhase(state?.status?.phase, "await_feedback") ||
            isPhase(state?.status?.phase, "processing_feedback")
              ? "border-blue-400 bg-blue-50"
              : isPhase(state?.status?.phase, "completed")
              ? "border-green-400 bg-green-50"
              : "border-gray-200"
          }`}>
          <div className="flex items-center gap-2">
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                isPhase(state?.status?.phase, "await_feedback") ||
                isPhase(state?.status?.phase, "processing_feedback")
                  ? "bg-blue-500 text-white"
                  : isPhase(state?.status?.phase, "completed")
                  ? "bg-green-500 text-white"
                  : "bg-gray-200"
              }`}>
              {isPhase(state?.status?.phase, "completed") ? "✓" : "3"}
            </span>
            <span className="font-medium text-sm">Feedback Phase</span>
          </div>
          {isPhase(state?.status?.phase, "processing_feedback") && (
            <p className="text-xs text-gray-600 mt-1 ml-7">
              The Recommendation Specialist is processing your feedback
            </p>
          )}
          {isPhase(state?.status?.phase, "await_feedback") && (
            <p className="text-xs text-gray-600 mt-1 ml-7">
              Awaiting your feedback on recommendations
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Recommendations display component
const RestaurantRecommendations = ({
  recommendations,
  restaurants,
}: {
  recommendations: string | null;
  restaurants: Restaurant[] | undefined;
}) => {
  return (
    <div className="recommendations-container">
      <div className="mb-6">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round">
            <path d="M18 8h1a4 4 0 0 1 0 8h-1"></path>
            <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path>
            <line x1="6" y1="1" x2="6" y2="4"></line>
            <line x1="10" y1="1" x2="10" y2="4"></line>
            <line x1="14" y1="1" x2="14" y2="4"></line>
          </svg>
          Recommended Restaurants
        </h3>
        {/* Display restaurant cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {restaurants &&
            restaurants.map((restaurant) => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
        </div>{" "}
        {/* Display detailed recommendations */}
        {recommendations && (
          <div className="prose prose-slate max-w-none">
            <ReactMarkdown
              components={{
                a: ({ node, ...props }) => (
                  <a
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                    {...props}
                  />
                ),
                h1: ({ node, ...props }) => (
                  <h1 className="text-2xl font-bold my-4" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-xl font-bold my-3" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-lg font-bold my-2" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc list-inside my-2" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal list-inside my-2" {...props} />
                ),
                li: ({ node, ...props }) => <li className="my-1" {...props} />,
              }}>
              {recommendations}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};

// FeedbackPrompt component to gather user feedback
const FeedbackPrompt = ({
  options,
  onSubmitFeedback,
  isProcessing,
}: {
  options: string[];
  onSubmitFeedback: (feedback: string) => void;
  isProcessing: boolean;
}) => {
  const [customFeedback, setCustomFeedback] = React.useState("");

  return (
    <div className="feedback-prompt mt-6 pt-4 border-t border-gray-200">
      <h4 className="text-lg font-semibold mb-3">
        Would you like more recommendations?
      </h4>{" "}
      <p className="text-sm text-gray-600 mb-3">
        Let us know if these recommendations meet your needs or if you&apos;d
        like to see more options.
      </p>
      <div className="feedback-options flex flex-wrap gap-2 mb-4">
        {options.map((option, idx) => (
          <button
            key={idx}
            onClick={() => onSubmitFeedback(option)}
            disabled={isProcessing}
            className="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md text-sm transition-colors disabled:opacity-50">
            {option}
          </button>
        ))}
      </div>
      <div className="custom-feedback mt-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={customFeedback}
            onChange={(e) => setCustomFeedback(e.target.value)}
            placeholder="Or type your own feedback..."
            disabled={isProcessing}
            className="flex-1 px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={() => {
              if (customFeedback.trim()) {
                onSubmitFeedback(customFeedback);
                setCustomFeedback("");
              }
            }}
            disabled={isProcessing || !customFeedback.trim()}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm disabled:opacity-50">
            Submit
          </button>
        </div>
      </div>
      {isProcessing && (
        <div className="mt-3 text-sm text-gray-600 flex items-center gap-2">
          <div className="animate-spin h-4 w-4 border-t-2 border-blue-500 rounded-full"></div>
          Processing your feedback...
        </div>
      )}
    </div>
  );
};

function RestaurantFinder() {
  // Reference to track if search is in progress
  const isSearchInProgress = useRef(false);

  // Connect to the agent's state using CopilotKit's useCoAgent hook
  const { state, stop: stopRestaurantAgent } =
    useCoAgent<RestaurantFinderAgentState>({
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
        },
        ui: { showRestaurants: false, showProgress: false, activeTab: "chat" },
      },
    });
  // Implement useCoAgentStateRender hook that allows you to render the state of the agent in the chat.
  useCoAgentStateRender({
    name: "restaurantFinderAgent",
    handler: ({
      nodeName,
      state: agentState,
    }: {
      nodeName: string;
      state: RestaurantFinderAgentState | undefined;
    }) => {
      // Stop the restaurant agent when the "__end__" node is reached
      if (nodeName === "__end__") {
        setTimeout(() => {
          isSearchInProgress.current = false; // Ensure flag is reset
          stopRestaurantAgent();
        }, 1000);
      }
    },
    render: ({
      status,
      state: agentState,
    }: {
      status: "inProgress" | "complete" | "error";
      state: RestaurantFinderAgentState | undefined;
    }) => {
      // Function to handle feedback submission directly from the chat
      const handleFeedbackSubmit = async (feedback: string) => {
        // You would typically use a sendMessage function from useCoAgent
        // For now, we'll just log it and let the CopilotSidebar component handle the actual submission
        console.log("Submitting feedback:", feedback);
      };

      if (status === "inProgress") {
        isSearchInProgress.current = true;
        return (
          <div className="search-in-progress bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            {/* Phase indicator at the top */}
            <div className="text-xs font-medium uppercase tracking-wide text-blue-500 mb-2">
              {agentState?.status?.phase === "research_phase" ||
              agentState?.status?.phase === "searching_restaurants"
                ? "Research Phase"
                : agentState?.status?.phase === "recommendation_phase" ||
                  agentState?.status?.phase === "generating_recommendations"
                ? "Recommendation Phase"
                : agentState?.status?.phase === "await_feedback" ||
                  agentState?.status?.phase === "processing_feedback"
                ? "Feedback Phase"
                : "Processing"}
            </div>

            <div className="flex items-center gap-2 mb-3">
              <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
              <p className="font-medium text-gray-800">
                {agentState?.status?.phase === "research_phase" ||
                agentState?.status?.phase === "searching_restaurants"
                  ? "Finding restaurants..."
                  : agentState?.status?.phase === "recommendation_phase" ||
                    agentState?.status?.phase === "generating_recommendations"
                  ? "Creating recommendations..."
                  : agentState?.status?.phase === "processing_feedback"
                  ? "Processing your feedback..."
                  : "Finding restaurants..."}
              </p>
            </div>

            <div className="status-container mb-3">
              <div className="flex items-center justify-between mb-1.5">
                {" "}
                <span className="text-sm text-gray-600">
                  {state?.status?.phase === "research_phase" ||
                  state?.status?.phase === "searching_restaurants"
                    ? "Research Phase: Searching for restaurants..."
                    : state?.status?.phase === "restaurants_found"
                    ? "Research Phase: Analyzing restaurant options..."
                    : state?.status?.phase === "recommendation_phase" ||
                      state?.status?.phase === "generating_recommendations"
                    ? "Recommendation Phase: Creating personalized suggestions..."
                    : state?.status?.phase === "processing_feedback"
                    ? "Processing your feedback..."
                    : "Processing..."}
                </span>
              </div>

              {state?.processing?.progress > 0 &&
                state?.processing?.progress < 1 && (
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full"
                      style={{
                        width: `${state.processing.progress * 100}%`,
                      }}></div>
                  </div>
                )}
            </div>

            {state?.search?.restaurants_found > 0 && (
              <div className="text-xs text-gray-500 flex items-center gap-1.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                Found {state.search.restaurants_found} restaurant
                {state.search.restaurants_found !== 1 ? "s" : ""}
              </div>
            )}
          </div>
        );
      }

      if (status === "complete") {
        isSearchInProgress.current = false; // Ensure the flag is reset
        // Don't return any UI here - let the main component handle showing recommendations
        return null;
      }

      return null;
    },
  });

  // When the search is complete and we have recommendations, show them
  if (
    state?.status?.phase === "completed" &&
    state?.processing?.recommendations
  ) {
    return (
      <div className="flex flex-col gap-4 h-full max-w-4xl mx-auto">
        <div className="p-6 bg-white border rounded-lg shadow-sm w-full">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              Restaurant Recommendations
            </h2>
            {state?.search?.query && (
              <div className="text-sm px-3 py-1.5 bg-blue-50 text-blue-800 border border-blue-100 rounded-md">
                Location:{" "}
                <span className="font-medium">{state.search.location}</span>
              </div>
            )}
          </div>

          <RestaurantRecommendations
            recommendations={state.processing.recommendations}
            restaurants={state.search.restaurants}
          />

          {/* Add controls for the recommendations */}
          <div className="mt-8 pt-4 border-t border-gray-200 flex justify-between">
            <button
              onClick={() => window.print()}
              className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2">
                <polyline points="6 9 6 2 18 2 18 9"></polyline>
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1-2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                <rect x="6" y="14" width="12" height="8"></rect>
              </svg>
              <span>Print Recommendations</span>
            </button>{" "}
            <button
              onClick={() =>
                navigator.clipboard.writeText(
                  state.processing.recommendations || ""
                )
              }
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md transition-colors">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
              </svg>
              <span>Copy to Clipboard</span>
            </button>
          </div>

          <FeedbackPrompt
            options={["More options", "Different location", "Other"]}
            onSubmitFeedback={(feedback) => console.log(feedback)}
            isProcessing={false}
          />
        </div>
      </div>
    );
  }

  // If search is in progress, show a loading state with enhanced UI
  if (
    state?.status &&
    state.status.phase !== "completed" &&
    (isSearchInProgress.current || state?.processing?.inProgress)
  ) {
    return (
      <div className="flex flex-col gap-4 h-full max-w-4xl mx-auto">
        <div className="p-6 bg-white border rounded-lg shadow-sm w-full">
          <h3 className="text-xl font-semibold mb-4">
            Finding Restaurants for You
          </h3>

          <div className="status-container mb-6">
            {" "}
            <div className="text-sm text-gray-600 mb-3">
              {state?.status?.phase === "searching_restaurants"
                ? `Searching for restaurants in ${state.search.location}...`
                : state?.status?.phase === "restaurants_found"
                ? "Analyzing restaurant options based on your preferences..."
                : state?.status?.phase === "generating_recommendations"
                ? "Creating personalized recommendations for you..."
                : "Processing your request..."}
            </div>
            {state?.processing?.progress > 0 && (
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-in-out"
                  style={{
                    width: `${Math.max(5, state.processing.progress * 100)}%`,
                  }}></div>
              </div>
            )}
          </div>

          <RestaurantProcessStages state={state} />

          {state?.search?.restaurants_found > 0 && (
            <div className="mt-6 text-sm text-gray-600 flex items-center gap-2">
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
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <span>
                Found {state.search.restaurants_found} restaurant
                {state.search.restaurants_found !== 1 ? "s" : ""}
              </span>
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
          <h3 className="text-xl font-semibold">Restaurant Finder</h3>
          <div className="text-sm px-3 py-1 bg-gray-100 rounded-full">
            Ready
          </div>
        </div>
        <div className="text-gray-600 mb-4">
          <p>
            Ask me to find restaurants in any location. I&apos;ll provide
            personalized recommendations based on your preferences.
          </p>
        </div>
        {/* Display restaurants when available */}
        {state?.ui?.showRestaurants &&
          state?.search?.restaurants &&
          state.search.restaurants.length > 0 && (
            <div className="restaurants-section mt-6 pt-4 border-t border-gray-200">
              <h4 className="text-lg font-medium mb-3">Found Restaurants</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {state.search.restaurants.map((restaurant) => (
                  <RestaurantCard key={restaurant.id} restaurant={restaurant} />
                ))}
              </div>
            </div>
          )}{" "}
        {state?.processing?.recommendations && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h4 className="text-lg font-medium mb-3">Recommendations</h4>
            <div className="prose prose-slate max-w-none">
              <ReactMarkdown
                components={{
                  a: ({ node, ...props }) => (
                    <a
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                      {...props}
                    />
                  ),
                  h1: ({ node, ...props }) => (
                    <h1 className="text-2xl font-bold my-4" {...props} />
                  ),
                  h2: ({ node, ...props }) => (
                    <h2 className="text-xl font-bold my-3" {...props} />
                  ),
                  h3: ({ node, ...props }) => (
                    <h3 className="text-lg font-bold my-2" {...props} />
                  ),
                  ul: ({ node, ...props }) => (
                    <ul className="list-disc list-inside my-2" {...props} />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol className="list-decimal list-inside my-2" {...props} />
                  ),
                  li: ({ node, ...props }) => (
                    <li className="my-1" {...props} />
                  ),
                }}>
                {state.processing.recommendations}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default RestaurantFinder;
