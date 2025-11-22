import type { Metadata } from "next";

import { CopilotKit } from "@copilotkit/react-core";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";

export const metadata: Metadata = {
  title: "Civic Grant Agent",
  description: "AI-powered grant finding and writing for fire departments and EMS agencies",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={"antialiased"}>
        <CopilotKit runtimeUrl="/copilotkit" agent="civic-grant-agent">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
