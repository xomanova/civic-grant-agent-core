import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";
 
// 1. You can use any service adapter here for multi-agent support. We use
//    the empty adapter since we're only using one agent.
const serviceAdapter = new ExperimentalEmptyAdapter();
 
// 2. Create the CopilotRuntime instance and utilize the AG-UI client
//    to setup the connection with the ADK agent.
// HARDCODED FOR DEBUGGING
const backendUrl = "https://civic-grant-agent-core.xomanova.io";
const runtime = new CopilotRuntime({
  agents: {
    // Our FastAPI endpoint URL
    "civic-grant-agent": new HttpAgent({url: `${backendUrl}/api/copilotkit`}),
  }   
});

// 3. Build a Next.js API route that handles the CopilotKit runtime requests.
export const POST = async (req: NextRequest) => {

  // 🔍 DEBUGGING LOGS
  console.log("--- COPILOTKIT DEBUG --- Configured Backend URL:", backendUrl);

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime, 
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
 
  return handleRequest(req);
};