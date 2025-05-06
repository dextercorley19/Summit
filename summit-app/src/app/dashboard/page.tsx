"use client"

import { useState } from "react"
import { BarChart2, GitBranch } from "lucide-react"
import { SidebarProvider } from "@/components/ui/sidebar"
import { RepositorySidebar } from "@/components/repository-sidebar"
import { ChatInterface } from "@/components/chat-interface"
import { AnalyticsPanel } from "@/components/analytics-panel"
import { UserAuth } from "@/components/user-auth"

export default function DashboardPage() {
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null)
  const [showAnalytics, setShowAnalytics] = useState(true)
  const [githubToken, setGithubToken] = useState<string | null>(null)

  return (
    <SidebarProvider>
      <div className="flex h-screen w-screen bg-background">
        <RepositorySidebar onSelectRepo={setSelectedRepo} githubToken={githubToken} />

        <div className="flex flex-1 flex-col overflow-hidden">
          <header className="border-b bg-background p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                <h1 className="text-lg font-semibold truncate max-w-[300px]">
                  {selectedRepo || "Select a Repository"}
                </h1>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowAnalytics(!showAnalytics)}
                  className="flex items-center gap-1 rounded-md px-2 py-1 text-sm hover:bg-accent"
                >
                  <BarChart2 className="h-4 w-4" />
                  <span className="hidden sm:inline">{showAnalytics ? "Hide Analytics" : "Show Analytics"}</span>
                </button>
                <UserAuth onAuthChange={setGithubToken} />
              </div>
            </div>
          </header>

          <div className="flex flex-1 overflow-hidden">
            <div
              className={`flex flex-1 ${
                showAnalytics ? "md:w-3/5" : "w-full"
              } flex-col overflow-hidden transition-all duration-200`}
            >
              <ChatInterface selectedRepo={selectedRepo} githubToken={githubToken} />
            </div>

            {showAnalytics && (
              <div className="hidden md:block md:w-2/5 border-l overflow-y-auto">
                <AnalyticsPanel selectedRepo={selectedRepo} githubToken={githubToken} />
              </div>
            )}
          </div>
        </div>
      </div>
    </SidebarProvider>
  )
}
