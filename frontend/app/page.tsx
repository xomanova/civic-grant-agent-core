"use client";

import { useCopilotReadable, useCopilotAction, useCoAgent, useCopilotChat } from "@copilotkit/react-core";
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
    population?: number;
    service_area_population?: number;
    service_area_size?: string;
  };
  organization_details?: {
    founded?: string;
    tax_id?: string;
    "501c3_status"?: boolean;
    budget?: number;
    annual_budget?: number;
    volunteers?: number;
    paid_staff?: number;
  };
  needs?: string | string[];
  equipment_inventory?: {
    summary?: string;
    condition?: string;
  };
  service_stats?: {
    calls?: number;
    active_members?: number;
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
  console.log("MainContent Rendering");
  // 1. State & Context
  const [departmentProfile, setDepartmentProfile] = useState<DepartmentProfile>({});
  const [grants, setGrants] = useState<Grant[]>([]);
  const [selectedGrant, setSelectedGrant] = useState<Grant | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  
  // Workflow state
  const [workflowStep, setWorkflowStep] = useState<string>("profile_building");
  const [profileComplete, setProfileComplete] = useState<boolean>(false); 
  
  // 2. Shared State with Backend via useCoAgent
  const { state: agentState } = useCoAgent<{
    civic_grant_profile: DepartmentProfile;
    profile_complete: boolean;
    workflow_step: string;
  }>({
    name: "civic-grant-agent",
    initialState: {
      civic_grant_profile: {},
      profile_complete: false,
      workflow_step: "profile_building"
    }
  });

  // 3. Track if agent is running
  const { isLoading } = useCopilotChat();

  // 4. SIMPLE RULE: Always sync FROM backend when agent state changes
  // The backend is the source of truth for workflow progression
  useEffect(() => {
    if (!agentState) return;
    
    console.log("agentState received:", {
      workflow_step: agentState.workflow_step,
      profile_complete: agentState.profile_complete,
      profile_keys: Object.keys(agentState.civic_grant_profile || {}),
      isLoading
    });
    localStorage.setItem("debug_agent_state", JSON.stringify(agentState));

    // Sync profile from backend (merge, don't replace)
    if (agentState.civic_grant_profile && Object.keys(agentState.civic_grant_profile).length > 0) {
      setDepartmentProfile(prev => {
        const newProfile = { ...prev, ...agentState.civic_grant_profile };
        if (JSON.stringify(prev) === JSON.stringify(newProfile)) return prev;
        console.log("Syncing profile from backend");
        return newProfile;
      });
    }
    
    // Sync workflow_step - only advance, never regress (unless it's a reset)
    if (agentState.workflow_step) {
      const stepOrder = ["profile_building", "grant_scouting", "grant_validation", "grant_writing"];
      setWorkflowStep(prev => {
        const prevIndex = stepOrder.indexOf(prev);
        const newIndex = stepOrder.indexOf(agentState.workflow_step);
        console.log(`workflow_step check: prev=${prev}(${prevIndex}), new=${agentState.workflow_step}(${newIndex})`);
        // Only update if advancing OR if it's explicitly profile_building (reset)
        if (newIndex > prevIndex || agentState.workflow_step === "profile_building") {
          if (prev !== agentState.workflow_step) {
            console.log(`✅ Syncing workflow_step: ${prev} -> ${agentState.workflow_step}`);
            return agentState.workflow_step;
          }
        } else {
          console.log(`⏸️ Not advancing workflow_step (would regress)`);
        }
        return prev;
      });
    }
    
    // Sync profile_complete - only set to true, never back to false (unless reset)
    if (agentState.profile_complete === true) {
      setProfileComplete(prev => {
        console.log(`profile_complete check: prev=${prev}, new=${agentState.profile_complete}`);
        if (!prev) {
          console.log("✅ Backend signaled profile completion");
          return true;
        }
        return prev;
      });
    } else {
      console.log(`profile_complete in agentState is ${agentState.profile_complete}, not syncing`);
    }
  }, [agentState, isLoading]);

  // 5. Persist to localStorage whenever state changes
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

  // 6. AGENT CONTEXT: Send state to the Agent via context
  // This ensures the backend always sees current frontend state
  useCopilotReadable({
    description: "The active Department Profile. If this is populated, the profile is considered 'in-progress' or 'complete'.",
    value: departmentProfile,
  });
  
  useCopilotReadable({
    description: "The list of Grants found so far.",
    value: grants,
  });
  
  useCopilotReadable({
    description: "Current workflow state - workflow_step indicates which phase we're in, profile_complete indicates if profile gathering is done.",
    value: { workflow_step: workflowStep, profile_complete: profileComplete },
  });

  // --- ACTIONS (Same logic, but state updates trigger the useEffects above) ---
  
  useCopilotAction({
    name: "handshake",
    description: "A test tool to verify backend-frontend connection",
    parameters: [],
    handler: async () => {
      console.log("🤝 Handshake received from Backend!");
      return "Handshake successful. Frontend is listening.";
    },
  });

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

  // Persist workflow state to localStorage
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem("workflow_step", workflowStep);
      localStorage.setItem("profile_complete", JSON.stringify(profileComplete));
    }
  }, [workflowStep, profileComplete, isLoaded]);

  // 1.5 HYDRATION: Load from LocalStorage on Mount
  useEffect(() => {
    const savedProfile = localStorage.getItem("civic_grant_profile");
    const savedGrants = localStorage.getItem("civic_grant_list");
    const savedWorkflowStep = localStorage.getItem("workflow_step");
    const savedProfileComplete = localStorage.getItem("profile_complete");

    if (savedWorkflowStep) {
      setWorkflowStep(savedWorkflowStep);
    }
    if (savedProfileComplete) {
      try {
        setProfileComplete(JSON.parse(savedProfileComplete));
      } catch (e) {
        console.error("Failed to parse profile_complete", e);
      }
    }
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

  // Prevent rendering until hydration is complete to avoid flicker
  if (!isLoaded) return <div className="p-10 text-center text-2xl">Loading Application State...</div>;

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <CopilotSidebar
        defaultOpen={true}
        labels={{
            title: "Grant Assistant",
            initial: "Hi! I'm here to help you find grants. Tell me about your department.",
        }}
      >
        <div className="p-8">
          <div className="max-w-4xl mx-auto">
            {/* View Switching Logic */}
            {departmentProfile.name ? (
              <DepartmentProfileView 
                profile={departmentProfile} 
                onClear={() => {
                  // CLEAR BYPASSES RELAY - always allowed
                  console.log("🗑️ CLEAR: Resetting all state (bypasses relay)");
                  setDepartmentProfile({});
                  setGrants([]);
                  setSelectedGrant(null);
                  setWorkflowStep("profile_building");
                  setProfileComplete(false);
                  localStorage.removeItem("civic_grant_profile");
                  localStorage.removeItem("civic_grant_list");
                  localStorage.removeItem("workflow_step");
                  localStorage.removeItem("profile_complete");
                  localStorage.removeItem("debug_agent_state");
                }}
              />
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

function DepartmentProfileView({ profile, onClear }: { profile: DepartmentProfile; onClear?: () => void }) {
  const hasBasicInfo = profile.name && profile.type && profile.location?.state;
  const hasOrgDetails = profile.organization_details?.budget || profile.organization_details?.annual_budget || profile.organization_details?.volunteers || profile.organization_details?.paid_staff;
  const hasNeeds = profile.needs && (typeof profile.needs === 'string' ? profile.needs.length > 0 : profile.needs.length > 0);
  const hasStats = profile.service_stats?.calls || profile.service_stats?.annual_fire_calls || profile.service_stats?.annual_ems_calls;
  
  // Normalize needs to always be an array for rendering
  const needsList = profile.needs 
    ? (typeof profile.needs === 'string' ? [profile.needs] : profile.needs)
    : [];

  return (
    <div className="bg-white rounded-lg shadow-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Department Profile</h2>
        <div className="flex items-center gap-2">
          {onClear && (
            <button
              onClick={onClear}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full hover:bg-gray-200 transition-colors"
              title="Clear profile"
            >
              ✕ Clear
            </button>
          )}
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
              {(profile.organization_details?.budget || profile.organization_details?.annual_budget) && (
                <div>
                  <span className="text-gray-500">Annual Budget:</span>
                  <span className="ml-2 font-medium">${(profile.organization_details?.budget || profile.organization_details?.annual_budget || 0).toLocaleString()}</span>
                </div>
              )}
              {profile.organization_details?.founded && (
                <div>
                  <span className="text-gray-500">Founded:</span>
                  <span className="ml-2 font-medium">{profile.organization_details.founded}</span>
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
              {needsList.map((need: string, idx: number) => (
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
              {(profile.service_stats?.calls !== undefined || profile.service_stats?.annual_fire_calls !== undefined) && (
                <div>
                  <span className="text-gray-500">Total Calls:</span>
                  <span className="ml-2 font-medium">{profile.service_stats?.calls || profile.service_stats?.annual_fire_calls}/year</span>
                </div>
              )}
              {profile.service_stats?.active_members !== undefined && (
                <div>
                  <span className="text-gray-500">Active Members:</span>
                  <span className="ml-2 font-medium">{profile.service_stats.active_members}</span>
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
