"use client"

import { useState, useEffect } from "react"
import { User, LogOut, Github, Key } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useToast } from "@/hooks/use-toast"

interface UserAuthProps {
  onAuthChange: (token: string | null) => void
}

export function UserAuth({ onAuthChange }: UserAuthProps) {
  const [isSignInOpen, setIsSignInOpen] = useState(false)
  const [token, setToken] = useState("")
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userInfo, setUserInfo] = useState<{ name: string; avatar_url: string } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  // Check for existing token in localStorage on component mount
  useEffect(() => {
    const storedToken = localStorage.getItem("github_token")
    if (storedToken) {
      setToken(storedToken)
      fetchUserInfo(storedToken)
    }
  }, [])

  const fetchUserInfo = async (accessToken: string) => {
    setIsLoading(true)
    try {
      const response = await fetch("https://api.github.com/user", {
        headers: {
          Authorization: `token ${accessToken}`, // Ensure token is prefixed with 'token '
        },
      })

      if (response.ok) {
        const data = await response.json()
        setUserInfo({
          name: data.name || data.login,
          avatar_url: data.avatar_url,
        })
        setIsAuthenticated(true)
        localStorage.setItem("github_token", accessToken)
        onAuthChange(accessToken)

        toast({
          title: "Successfully authenticated",
          description: `Welcome, ${data.name || data.login}!`,
        })
      } else {
        throw new Error("Authentication failed")
      }
    } catch (error) {
      console.error("Authentication error:", error)
      setIsAuthenticated(false)
      setUserInfo(null)
      localStorage.removeItem("github_token")

      toast({
        title: "Authentication failed",
        description: "Please check your Personal Access Token and try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setIsSignInOpen(false)
    }
  }

  const handleSignIn = () => {
    if (token.trim()) {
      fetchUserInfo(token)
    }
  }

  const handleSignOut = () => {
    setIsAuthenticated(false)
    setUserInfo(null)
    setToken("")
    localStorage.removeItem("github_token")
    onAuthChange(null)

    toast({
      title: "Signed out",
      description: "You have been signed out successfully.",
    })
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="relative h-8 w-8 rounded-full">
            {isAuthenticated && userInfo ? (
              <Avatar className="h-8 w-8">
                <AvatarImage src={userInfo.avatar_url || "/placeholder.svg"} alt={userInfo.name} />
                <AvatarFallback>{userInfo.name.charAt(0)}</AvatarFallback>
              </Avatar>
            ) : (
              <User className="h-5 w-5" />
            )}
            {isAuthenticated && (
              <span className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full bg-green-500 border-2 border-background" />
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {isAuthenticated && userInfo ? (
            <>
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{userInfo.name}</p>
                  <p className="text-xs leading-none text-muted-foreground">GitHub User</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleSignOut}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Sign out</span>
              </DropdownMenuItem>
            </>
          ) : (
            <>
              <DropdownMenuLabel>GitHub Authentication</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => setIsSignInOpen(true)}>
                <Github className="mr-2 h-4 w-4" />
                <span>Sign in with GitHub</span>
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={isSignInOpen} onOpenChange={setIsSignInOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>GitHub Authentication</DialogTitle>
            <DialogDescription>Enter your GitHub Personal Access Token to access your repositories.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="token">Personal Access Token</Label>
              <div className="flex items-center space-x-2">
                <Key className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="token"
                  type="password"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Your token needs <code>repo</code> scope permissions.
                <a
                  href="https://github.com/settings/tokens/new"
                  target="_blank"
                  rel="noreferrer"
                  className="ml-1 text-primary underline"
                >
                  Create a token
                </a>
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSignInOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSignIn} disabled={!token.trim() || isLoading}>
              {isLoading ? "Authenticating..." : "Sign In"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
