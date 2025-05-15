// Define a type for restaurant result items
export type Restaurant = {
  id: string;
  name: string;
  cuisine?: string;
  address?: string;
  priceRange?: string;
  rating?: string;
  url?: string;
  imageUrl?: string;
};

// Define the restaurant finder agent state type
export interface RestaurantFinderAgentState {
  status: {
    phase:
      | "idle"
      | "initialized"
      | "searching_restaurants"
      | "restaurants_found"
      | "presenting_recommendations"
      | "await_feedback"
      | "processing_feedback"
      | "completed"
      | "feedback_completed";
    error: string | null;
    timestamp?: string;
  };
  search: {
    query: string;
    location: string;
    stage:
      | "not_started"
      | "searching"
      | "found"
      | "analyzing"
      | "recommending"
      | "feedback"
      | "complete";
    restaurants_found: number;
    restaurants?: Restaurant[];
    completed: boolean;
  };
  processing: {
    progress: number;
    phases: string[];
    currentPhase: string;
    recommendations: string | null;
    completed: boolean;
    inProgress: boolean;
    feedback?: string | null;
  };
  ui: {
    showRestaurants: boolean;
    showProgress: boolean;
    activeTab: string;
    showFeedbackPrompt?: boolean;
    feedbackOptions?: string[];
  };
}
