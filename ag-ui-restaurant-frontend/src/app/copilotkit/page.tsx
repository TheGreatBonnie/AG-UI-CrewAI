"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import RestaurantFinder from "../components/RestaurantFinder";

/**
 * CopilotKitPage component that serves as the main page with the CopilotSidebar
 * and includes the RestaurantActionProvider for all Generative UI capabilities
 */
export default function CopilotKitPage() {
  return (
    <main className="flex h-screen">
      <div className="flex-1 p-6 overflow-auto">
        <RestaurantFinder />
      </div>

      <CopilotSidebar
        clickOutsideToClose={false}
        defaultOpen={true}
        labels={{
          title: "Restaurant Finder",
          initial:
            "Hi! I'm your restaurant finding assistant. Ask me to find restaurants in any location, and I'll help you discover great dining options.",
        }}
      />
    </main>
  );
}
