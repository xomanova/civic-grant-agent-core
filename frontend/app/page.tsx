"use client";

import { useCopilotReadable, useCopilotAction, useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useState, useEffect } from "react";

// --- Interfaces (Same as before) ---
interface DepartmentProfile {
  name?: string;
  type?: string;
  location?: {
    state?: string;
    county?: string;
    city?: string;
    service_area_population?: number;
    service_area_size?: string;
  };
  organization_details?: {
    founded?: string;
    tax_id?: string;
    "501c3_status"?: boolean;
    annual_budget?: number;
    volunteers?: number;
    paid_staff?: number;
  };
  needs?: string[];
  equipment_inventory?: {
    summary?: string;
    condition?: string;
  };
  service_stats?: {
    annual_fire_calls?: number;
    annual_ems_calls?: number;
    mutual_aid_responses?: number;
    average_response_time_minutes?: number;
  };
  mission?: string;
  community_impact?: string;
}

interface Grant {
  name: string;
  source: string;
  url: string;
  description: string;
  funding_range?: string;
  deadline?: string;
  eligibility_score?: number;
  match_reasons?: string[];
  priority_rank?: number;
}

export default function Home() {
  return <MainContent />;
}

function MainContent() {
  // 1. Initialize State
  const [departmentProfile, setDepartmentProfile] = useState<DepartmentProfile>({});
  const [grants, setGrants] = useState<Grant[]>([]);
  const [selectedGrant, setSelectedGrant] = useState<Grant | null>(null);
  const [isLoaded, setIsLoaded] = useState(false); // Avoid hydration mismatch

  // 2. HYDRATION: Load from LocalStorage on Mount
  useEffect(() => {
    const savedProfile = localStorage.getItem("civic_grant_profile");
    const savedGrants = localStorage.getItem("civic_grant_list");

    if (savedProfile) {
      try {
        setDepartmentProfile(JSON.parse(savedProfile));
      } catch (e) {
        console.error("Failed to parse profile", e);
      }
    }
    if (savedGrants) {
      try {
        setGrants(JSON.parse(savedGrants));
      } catch (e) {
        console.error("Failed to parse grants", e);
      }
    }
    setIsLoaded(true);
  }, []);

  // 3. PERSISTENCE: Save to LocalStorage whenever state changes
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem("civic_grant_profile", JSON.stringify(departmentProfile));
    }
  }, [departmentProfile, isLoaded]);

  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem("civic_grant_list", JSON.stringify(grants));
    }
  }, [grants, isLoaded]);

  // 4. AGENT CONTEXT: Send the profile to the Agent
  // This ensures that even if the backend restarts, the Agent "sees" the data 
  // immediately because it is injected into the context window.
  useCopilotReadable({
    description: "The active Department Profile. If this is populated, the profile is considered 'in-progress' or 'complete'.",
    value: departmentProfile,
  });
  
  useCopilotReadable({
    description: "The list of Grants found so far.",
    value: grants,
  });

  // 5. COAGENT: Sync Backend State
  const { state: agentState } = useCoAgent({
    name: "CivicGrantAgent",
    initialState: {
      department_profile: departmentProfile,
    },
  });

  useEffect(() => {
    if (agentState?.department_profile && Object.keys(agentState.department_profile).length > 0) {
      setDepartmentProfile(agentState.department_profile);
    }
  }, [agentState]);

  // --- ACTIONS (Same logic, but state updates trigger the useEffects above) ---
  
  useCopilotAction({
    name: "updateDepartmentProfile",
    description: "Update the department profile with new information",
    parameters: [
      {
        name: "profileData",
        type: "object",
        description: "Partial or complete department profile data",
      },
    ],
    handler: async ({ profileData }: { profileData: Partial<DepartmentProfile> }) => {
      setDepartmentProfile((prev) => {
        // Deep merge logic for nested objects
        return {
          ...prev,
          ...profileData,
          location: { ...prev.location, ...profileData.location },
          organization_details: { ...prev.organization_details, ...profileData.organization_details },
          equipment_inventory: { ...prev.equipment_inventory, ...profileData.equipment_inventory },
          service_stats: { ...prev.service_stats, ...profileData.service_stats },
        };
      });
      return "Profile updated in frontend.";
    },
  });

  useCopilotAction({
    name: "updateGrantsList",
    description: "Update the list of found grants",
    parameters: [{ name: "grantsList", type: "object[]" }],
    handler: async ({ grantsList }: { grantsList: Grant[] }) => {
      setGrants(grantsList);
      return "Grants list updated in frontend.";
    },
  });

  useCopilotAction({
    name: "selectGrantForApplication",
    description: "User selected a grant to generate an application for",
    parameters: [{ name: "grantName", type: "string" }],
    handler: async ({ grantName }: { grantName: string }) => {
      const grant = grants.find((g) => g.name === grantName);
      if (grant) setSelectedGrant(grant);
      return `Selected grant: ${grantName}`;
    },
  });

  // Prevent rendering until hydration is complete to avoid flicker
  if (!isLoaded) return null;

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <CopilotSidebar
        defaultOpen={true}
        // OPTIONAL: You can persist the chat history ID here too if you want the *conversation* to survive reload
        // labels={{ ... }}
      >
        <div className="p-8">
          <div className="max-w-4xl mx-auto">
            {/* View Switching Logic */}
            {departmentProfile.name ? (
              <DepartmentProfileView profile={departmentProfile} />
            ) : (
              <WelcomeView />
            )}
            
            {grants.length > 0 && (
              <GrantsView 
                grants={grants} 
                onSelectGrant={(grant) => setSelectedGrant(grant)}
                selectedGrant={selectedGrant}
              />
            )}
          </div>
        </div>
      </CopilotSidebar>
    </main>
  );
}

function WelcomeView() {
  return (
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
            Open the sidebar to get started with your grant search! 👉 
          </p>
        </div>
      </div>
    </div>
  );
}

function DepartmentProfileView({ profile }: { profile: DepartmentProfile }) {
  const hasBasicInfo = profile.name && profile.type && profile.location?.state;
  const hasOrgDetails = profile.organization_details?.annual_budget || profile.organization_details?.volunteers || profile.organization_details?.paid_staff;
  const hasNeeds = profile.needs && profile.needs.length > 0;
  const hasStats = profile.service_stats?.annual_fire_calls || profile.service_stats?.annual_ems_calls;

  return (
    <div className="bg-white rounded-lg shadow-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Department Profile</h2>
        <div className="flex items-center gap-2">
          {hasBasicInfo && <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">✓ Basic Info</span>}
          {hasOrgDetails && <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">✓ Organization</span>}
          {hasNeeds && <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">✓ Needs</span>}
          {hasStats && <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">✓ Statistics</span>}
        </div>
      </div>

      <div className="space-y-4">
        {/* Basic Information */}
        {profile.name && (
          <div className="border-b pb-3">
            <h3 className="text-xl font-semibold text-gray-800">{profile.name}</h3>
            {profile.type && (
              <p className="text-sm text-gray-600 mt-1">
                {profile.type.charAt(0).toUpperCase() + profile.type.slice(1)} Department
              </p>
            )}
          </div>
        )}

        {/* Location */}
        {profile.location && (profile.location.city || profile.location.state) && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-1">📍 Location</h4>
            <p className="text-gray-600">
              {[profile.location.city, profile.location.county, profile.location.state].filter(Boolean).join(", ")}
            </p>
            {profile.location.service_area_population && (
              <p className="text-sm text-gray-500 mt-1">
                Population: {profile.location.service_area_population.toLocaleString()}
              </p>
            )}
          </div>
        )}

        {/* Organization Details */}
        {hasOrgDetails && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">🏢 Organization</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {profile.organization_details?.annual_budget && (
                <div>
                  <span className="text-gray-500">Annual Budget:</span>
                  <span className="ml-2 font-medium">${profile.organization_details.annual_budget.toLocaleString()}</span>
                </div>
              )}
              {profile.organization_details?.volunteers !== undefined && (
                <div>
                  <span className="text-gray-500">Volunteers:</span>
                  <span className="ml-2 font-medium">{profile.organization_details.volunteers}</span>
                </div>
              )}
              {profile.organization_details?.paid_staff !== undefined && (
                <div>
                  <span className="text-gray-500">Paid Staff:</span>
                  <span className="ml-2 font-medium">{profile.organization_details.paid_staff}</span>
                </div>
              )}
              {profile.organization_details?.["501c3_status"] !== undefined && (
                <div>
                  <span className="text-gray-500">501(c)(3):</span>
                  <span className="ml-2 font-medium">{profile.organization_details["501c3_status"] ? "Yes" : "No"}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Primary Needs */}
        {hasNeeds && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">🎯 Primary Needs</h4>
            <ul className="list-disc list-inside space-y-1">
              {profile.needs!.map((need, idx) => (
                <li key={idx} className="text-gray-600 text-sm">{need}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Service Statistics */}
        {hasStats && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">📊 Service Statistics</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {profile.service_stats?.annual_fire_calls !== undefined && (
                <div>
                  <span className="text-gray-500">Fire Calls:</span>
                  <span className="ml-2 font-medium">{profile.service_stats.annual_fire_calls}/year</span>
                </div>
              )}
              {profile.service_stats?.annual_ems_calls !== undefined && (
                <div>
                  <span className="text-gray-500">EMS Calls:</span>
                  <span className="ml-2 font-medium">{profile.service_stats.annual_ems_calls}/year</span>
                </div>
              )}
              {profile.service_stats?.average_response_time_minutes !== undefined && (
                <div>
                  <span className="text-gray-500">Avg Response:</span>
                  <span className="ml-2 font-medium">{profile.service_stats.average_response_time_minutes} min</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Mission */}
        {profile.mission && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-1">💡 Mission</h4>
            <p className="text-gray-600 text-sm">{profile.mission}</p>
          </div>
        )}
      </div>

      {!hasBasicInfo && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-blue-900 text-sm">
            Continue chatting to complete your profile...
          </p>
        </div>
      )}
    </div>
  );
}

function GrantsView({ grants, onSelectGrant, selectedGrant }: { 
  grants: Grant[]; 
  onSelectGrant: (grant: Grant) => void;
  selectedGrant: Grant | null;
}) {
  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Found Grants</h2>
        <span className="px-3 py-1 bg-green-100 text-green-700 font-semibold rounded-full">
          {grants.length} {grants.length === 1 ? 'Grant' : 'Grants'}
        </span>
      </div>

      <div className="space-y-3">
        {grants.map((grant, idx) => (
          <div
            key={idx}
            onClick={() => onSelectGrant(grant)}
            className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
              selectedGrant?.name === grant.name 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {grant.priority_rank && (
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-semibold rounded">
                      #{grant.priority_rank}
                    </span>
                  )}
                  <h3 className="font-semibold text-gray-900">{grant.name}</h3>
                </div>
                <p className="text-sm text-gray-600 mb-2">{grant.source}</p>
                <p className="text-sm text-gray-700 mb-2">{grant.description}</p>
                
                {grant.funding_range && (
                  <p className="text-sm text-green-600 font-medium mb-2">
                    💰 {grant.funding_range}
                  </p>
                )}

                {grant.deadline && (
                  <p className="text-xs text-gray-500 mb-2">
                    📅 {grant.deadline}
                  </p>
                )}

                {grant.eligibility_score && (
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all"
                        style={{ width: `${grant.eligibility_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-semibold text-gray-700">
                      {Math.round(grant.eligibility_score * 100)}% match
                    </span>
                  </div>
                )}

                {grant.match_reasons && grant.match_reasons.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-gray-600 mb-1">Why this matches:</p>
                    <ul className="text-xs text-gray-600 space-y-0.5">
                      {grant.match_reasons.map((reason, i) => (
                        <li key={i}>✓ {reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelectGrant(grant);
              }}
              className="mt-3 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
            >
              Generate Application
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
