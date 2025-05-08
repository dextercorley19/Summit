"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, ArrowDown, GitBranch } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/hooks/use-toast"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface ChatInterfaceProps {
  selectedRepo: string | null
  githubToken?: string | null
}

export function ChatInterface({ selectedRepo, githubToken }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()
  const [conversationId, setConversationId] = useState<string | null>(null)

  // Add welcome message when repo is selected and clear conversation ID
  useEffect(() => {
    if (selectedRepo) {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: `Welcome to the ${selectedRepo} repository chat! I will focus on analyzing the existing files and structure within this repository. How can I assist you today?`,
          timestamp: new Date(),
        },
      ])
      setConversationId(null) // Reset conversation ID when repo changes
    } else {
      setMessages([])
      setConversationId(null)
    }
  }, [selectedRepo])

  // Scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  // Handle scroll to detect when we're not at the bottom
  const handleScroll = () => {
    if (scrollAreaRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollAreaRef.current
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
      setShowScrollButton(!isAtBottom)
    }
  }

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedRepo) return
    if (!githubToken) {
      toast({
        title: "Authentication required",
        description: "Please sign in with GitHub to use the chat feature",
        variant: "destructive",
      })
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Call the backend API for chat
      // TODO: Replace with environment variable for backend URL
      const backendApiUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendApiUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${githubToken}`, // Added Authorization header
        },
        body: JSON.stringify({
          question: input,
          repository: selectedRepo,
          messages: messages.map(msg => ({ role: msg.role, content: msg.content })), // Send previous messages
          conversation_id: conversationId, // Send conversation ID
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || "Sorry, I couldn't analyze that. Please try again.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
      if (data.conversation_id) {
        setConversationId(data.conversation_id) // Store new/updated conversation ID
      }
    } catch (error) {
      console.error("Chat error:", error)

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, there was an error processing your request. Please try again later.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])

      toast({
        title: "Chat error",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (!selectedRepo) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center max-w-md mx-auto">
          <GitBranch className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
          <h3 className="text-lg font-medium">No Repository Selected</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Select a repository from the sidebar to start a conversation
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <ScrollArea ref={scrollAreaRef} onScroll={handleScroll} className="flex-1 p-4">
        <div className="mx-auto max-w-3xl">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 flex ${message.role === "assistant" ? "justify-start" : "justify-end"}`}
            >
              <div
                className={`flex max-w-[80%] rounded-lg p-4 ${
                  message.role === "assistant"
                    ? "bg-accent text-accent-foreground"
                    : "bg-primary text-primary-foreground"
                }`}
              >
                <div className="mr-3 mt-1">
                  {message.role === "assistant" ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
                </div>
                <div>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className="mt-1 text-xs opacity-70">{message.timestamp.toLocaleTimeString()}</div>
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="mb-4 flex justify-start">
              <div className="flex max-w-[80%] rounded-lg bg-accent p-4 text-accent-foreground">
                <div className="mr-3 mt-1">
                  <Bot className="h-5 w-5" />
                </div>
                <div className="flex items-center">
                  <div className="dot-flashing"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {showScrollButton && (
        <Button
          variant="outline"
          size="icon"
          className="absolute bottom-24 right-8 rounded-full shadow-md"
          onClick={scrollToBottom}
        >
          <ArrowDown className="h-4 w-4" />
        </Button>
      )}

      <div className="border-t bg-background p-4">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                githubToken
                  ? "Ask about your repository..."
                  : "Sign in with GitHub to ask questions about this repository"
              }
              className="min-h-24 resize-none"
              disabled={!githubToken}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!input.trim() || isLoading || !githubToken}
              className="h-10 w-10 rounded-full p-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
