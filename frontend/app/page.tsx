"use client";

import { CopilotKit, useCoAgent, useCopilotAction } from "@copilotkit/react-core";
import { CopilotKitCSSProperties, CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useState } from "react";

export default function Home() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="civic-grant-agent">
      <MainContent />
    </CopilotKit>
  );
}

function MainContent() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <CopilotSidebar
        defaultOpen={true}
        labels={{
          title: "🚒 Civic Grant Agent",
          initial: "Hi! I'm here to help you find grants for your fire department or EMS agency. To get started, could you tell me your organization's name and what type of department you are (volunteer, paid, or combination)?",
        }}
      >
        <div className="p-8">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-xl p-8">
              <div className="flex items-center gap-4 mb-6">
                <div className="text-6xl">🚒</div>
                <div>
                  <h1 className="text-4xl font-bold text-gray-900">
                    Civic Grant Agent
                  </h1>
                  <p className="text-lg text-gray-600 mt-2">
                    AI-powered grant finding for fire departments & EMS agencies
                  </p>
                </div>
              </div>

              <div className="border-t pt-6">
                <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                  How It Works
                </h2>
                
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center font-semibold text-blue-700">
                      1
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Profile Your Department</h3>
                      <p className="text-gray-600">Tell us about your organization, location, budget, and equipment needs</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center font-semibold text-blue-700">
                      2
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Find Matching Grants</h3>
                      <p className="text-gray-600">Our AI searches for grants that match your specific needs and location</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center font-semibold text-blue-700">
                      3
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Validate Eligibility</h3>
                      <p className="text-gray-600">We check grant requirements against your profile to ensure you qualify</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center font-semibold text-blue-700">
                      4
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Draft Your Application</h3>
                      <p className="text-gray-600">Get help writing compelling grant applications tailored to each opportunity</p>
                    </div>
                  </div>
                </div>

                <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-blue-900 font-medium">
                    👈 Open the sidebar to get started with your grant search!
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CopilotSidebar>
    </main>
  );
}
