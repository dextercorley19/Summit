"use client"

import { useState, useEffect } from "react"
import { GitBranch, Code, Settings, MoreHorizontal, AlertCircle } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
  SidebarInput,
  SidebarMenuAction,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { useToast } from "@/hooks/use-toast"
import { API_BASE_URL } from "@/lib/utils"

interface Repository {
  full_name: string
  owner: string
  name: string
  branches?: string[]
  lastActive?: string
}

interface RepositorySidebarProps {
  onSelectRepo: (repo: string) => void
  githubToken: string | null
}

export function RepositorySidebar({ onSelectRepo, githubToken }: RepositorySidebarProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null)
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [filteredRepos, setFilteredRepos] = useState<Repository[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Fetch repositories when token changes
  useEffect(() => {
    if (githubToken) {
      fetchRepositories()
    } else {
      // Reset to empty when not authenticated
      setRepositories([])
      setFilteredRepos([])
    }
  }, [githubToken])

  // Update filtered repos when search query changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredRepos(repositories)
      return
    }

    const filtered = repositories.filter(
      (repo) =>
        repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        repo.owner.toLowerCase().includes(searchQuery.toLowerCase()),
    )
    setFilteredRepos(filtered)
  }, [searchQuery, repositories])

  const fetchRepositories = async () => {
    if (!githubToken) return

    setIsLoading(true)
    setError(null)

    try {
      console.log("Fetching repositories from:", `${API_BASE_URL}/api/repositories`);
      console.log("Using GitHub token:", githubToken ? "Token exists" : "No token");
      
      // Use our backend API instead of directly calling GitHub
      const response = await fetch(`${API_BASE_URL}/api/repositories`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "GitHub-Token": githubToken,
        },
      });

      console.log("Response status:", response.status);
      console.log("Response ok:", response.ok);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch repositories: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json()

      // Check if data is already an array (direct response format)
      if (Array.isArray(data)) {
        const formattedRepos = data.map((repo: any) => ({
          full_name: repo.full_name,
          owner: repo.full_name.split('/')[0],
          name: repo.name,
          branches: repo.branches || ["main"],
          lastActive: repo.lastActive || "Recently updated",
        }))
        
        setRepositories(formattedRepos)
        setFilteredRepos(formattedRepos)
      }
      // Check for data.repositories format
      else if (data.repositories && Array.isArray(data.repositories)) {
        const formattedRepos = data.repositories.map((repo: Repository) => ({
          ...repo,
          branches: repo.branches || ["main"],
          lastActive: repo.lastActive || "Recently updated",
        }))

        setRepositories(formattedRepos)
        setFilteredRepos(formattedRepos)
      } else {
        throw new Error("Invalid response format")
      }
    } catch (error) {
      console.error("Error fetching repositories:", error)
      setError("Failed to load repositories")

      toast({
        title: "Error loading repositories",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      })

      // Set empty repositories
      setRepositories([])
      setFilteredRepos([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleRepoSelect = (repoName: string, owner: string) => {
    const fullName = `${owner}/${repoName}`
    setSelectedRepo(fullName)
    onSelectRepo(fullName)
  }

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center justify-between p-2">
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            <h2 className="text-base font-semibold">Repositories</h2>
          </div>
        </div>
        <div className="px-2 pb-2">
          <SidebarInput
            placeholder="Search repositories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            {githubToken ? "Your GitHub Repositories" : "Sign in to view repositories"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            {isLoading ? (
              <div className="p-3 text-center text-sm text-muted-foreground">
                <div className="animate-spin mb-2 mx-auto h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                Loading repositories...
              </div>
            ) : error ? (
              <div className="p-3 text-center text-sm text-destructive">
                <AlertCircle className="h-4 w-4 mx-auto mb-1" />
                {error}
              </div>
            ) : !githubToken ? (
              <div className="p-3 text-center text-sm text-muted-foreground">
                Please sign in with GitHub to view your repositories
              </div>
            ) : filteredRepos.length === 0 ? (
              <div className="p-3 text-center text-sm text-muted-foreground">
                {searchQuery ? "No matching repositories found" : "No repositories found"}
              </div>
            ) : (
              <SidebarMenu>
                {filteredRepos.map((repo) => (
                  <SidebarMenuItem key={`${repo.owner}/${repo.name}`}>
                    <DropdownMenu>
                      <SidebarMenuButton
                        isActive={selectedRepo === `${repo.owner}/${repo.name}`}
                        onClick={() => handleRepoSelect(repo.name, repo.owner)}
                        tooltip={`Last active: ${repo.lastActive}`}
                      >
                        <Code className="h-4 w-4" />
                        <span>{repo.name}</span>
                      </SidebarMenuButton>
                      <DropdownMenuTrigger asChild>
                        <SidebarMenuAction showOnHover>
                          <MoreHorizontal className="h-4 w-4" />
                        </SidebarMenuAction>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" side="right">
                        <DropdownMenuItem>
                          <Settings className="mr-2 h-4 w-4" />
                          <span>Repository Settings</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <GitBranch className="mr-2 h-4 w-4" />
                          <span>View Branches</span>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>

                    <SidebarMenuSub>
                      {repo.branches?.map((branch) => (
                        <SidebarMenuSubItem key={branch}>
                          <SidebarMenuSubButton>
                            <GitBranch className="h-3 w-3" />
                            <span>{branch}</span>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            )}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="p-2">
          <Button className="w-full" size="sm" disabled={!githubToken} onClick={fetchRepositories}>
            <GitBranch className="mr-2 h-4 w-4" />
            Refresh Repositories
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
