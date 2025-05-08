"use client"

import { useState, useEffect } from "react"
import { BarChart2, Code, AlertTriangle, AlertCircle } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast"

interface AnalyticsPanelProps {
  selectedRepo: string | null
  githubToken?: string | null
}

interface CodeQualityResponse {
  overall_score: number
  file_analyses: Record<string, FileAnalysis>
  summary: string
}

interface FileAnalysis {
  lint_score: number
  chunks: Record<string, ChunkAnalysis>
  recent_changes: string
  insights: string
  suggestions: string
  repo_context: string
}

interface ChunkAnalysis {
  content_type: string
  context: string
  quality_score: number
  insights: string
  suggestions: string
}

export function AnalyticsPanel({ selectedRepo, githubToken }: AnalyticsPanelProps) {
  const [activeTab, setActiveTab] = useState("overview")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [analysisData, setAnalysisData] = useState<CodeQualityResponse | null>(null)
  const { toast } = useToast()

  // Fetch analysis data when repository changes
  useEffect(() => {
    if (selectedRepo && githubToken) {
      fetchAnalysisData()
    } else {
      setAnalysisData(null)
    }
  }, [selectedRepo, githubToken])

  const fetchAnalysisData = async () => {
    if (!selectedRepo || !githubToken) return

    setIsLoading(true)
    setError(null)

    try {
      // Call the backend API for repository analysis
      // TODO: Replace with environment variable for backend URL and ensure this endpoint exists on backend-old
      const backendApiUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendApiUrl}/api/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${githubToken}`, // Added Authorization header
        },
        body: JSON.stringify({
          repository: selectedRepo,
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()
      setAnalysisData(data)
    } catch (error) {
      console.error("Analysis error:", error)
      setError(error instanceof Error ? error.message : "Unknown error occurred")

      toast({
        title: "Analysis error",
        description: error instanceof Error ? error.message : "Failed to analyze repository",
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
          <BarChart2 className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
          <h3 className="text-lg font-medium">No Repository Selected</h3>
          <p className="mt-1 text-sm text-muted-foreground">Select a repository to view analytics</p>
        </div>
      </div>
    )
  }

  if (!githubToken) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center max-w-md mx-auto">
          <AlertCircle className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
          <h3 className="text-lg font-medium">Authentication Required</h3>
          <p className="mt-1 text-sm text-muted-foreground">Please sign in with GitHub to view repository analytics</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center max-w-md mx-auto">
          <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <h3 className="text-lg font-medium">Analyzing Repository</h3>
          <p className="mt-1 text-sm text-muted-foreground">This may take a moment as we analyze your code...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-destructive" />
          <h3 className="mt-4 text-lg font-medium text-destructive">Analysis Error</h3>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
          <Button variant="outline" className="mt-4" onClick={fetchAnalysisData}>
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  if (!analysisData) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center">
          <BarChart2 className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium">No Analysis Data</h3>
          <p className="mt-2 text-sm text-muted-foreground">Click the button below to analyze this repository</p>
          <Button className="mt-4" onClick={fetchAnalysisData}>
            Analyze Repository
          </Button>
        </div>
      </div>
    )
  }

  // Calculate language distribution from file analyses
  const languageDistribution = calculateLanguageDistribution(analysisData.file_analyses)

  return (
    <div className="h-full p-4">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">{selectedRepo} Analytics</h2>
        <p className="text-sm text-muted-foreground">Code quality and repository metrics</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="code">Code Quality</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 pt-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Files Analyzed</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Object.keys(analysisData.file_analyses).length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analysisData.overall_score.toFixed(1)}/10</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Language Distribution</CardTitle>
              <CardDescription>Code breakdown by language</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {languageDistribution.map((lang) => (
                  <div key={lang.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: lang.color }} />
                        <span>{lang.name}</span>
                      </div>
                      <span className="text-sm">{lang.percentage}%</span>
                    </div>
                    <Progress value={lang.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-line text-sm">{analysisData.summary}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="code" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Code Quality Score</CardTitle>
              <CardDescription>Overall repository health</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center py-4">
                <div
                  className={`relative flex h-40 w-40 items-center justify-center rounded-full border-8 ${getScoreColor(analysisData.overall_score)}`}
                >
                  <span className="text-4xl font-bold">{getLetterGrade(analysisData.overall_score)}</span>
                </div>
              </div>

              <div className="mt-4 space-y-4">
                {Object.entries(analysisData.file_analyses)
                  .slice(0, 3)
                  .map(([filePath, analysis]) => (
                    <div key={filePath} className="flex items-center justify-between">
                      <div className="flex items-center gap-2 truncate">
                        <Code className="h-4 w-4 text-blue-500 shrink-0" />
                        <span className="truncate">{getFileName(filePath)}</span>
                      </div>
                      <span className="font-medium">{analysis.lint_score.toFixed(1)}/10</span>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Issues by Severity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {calculateIssuesBySeverity(analysisData.file_analyses).map((issue) => (
                  <div key={issue.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: issue.color }} />
                        <span>{issue.name}</span>
                      </div>
                      <span className="text-sm">{issue.count}</span>
                    </div>
                    <Progress value={issue.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Changes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analysisData.file_analyses)
                  .slice(0, 5)
                  .map(([filePath, analysis]) => (
                    <div key={filePath} className="space-y-2">
                      <div className="font-medium">{getFileName(filePath)}</div>
                      <p className="text-sm text-muted-foreground">{analysis.recent_changes}</p>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Improvement Suggestions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analysisData.file_analyses)
                  .slice(0, 3)
                  .map(([filePath, analysis]) => (
                    <div key={filePath} className="space-y-2">
                      <div className="font-medium">{getFileName(filePath)}</div>
                      <p className="text-sm text-muted-foreground">{analysis.suggestions}</p>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

// Helper functions
function getFileName(path: string): string {
  return path.split("/").pop() || path
}

function getLetterGrade(score: number): string {
  if (score >= 9.5) return "A+"
  if (score >= 9.0) return "A"
  if (score >= 8.5) return "A-"
  if (score >= 8.0) return "B+"
  if (score >= 7.5) return "B"
  if (score >= 7.0) return "B-"
  if (score >= 6.5) return "C+"
  if (score >= 6.0) return "C"
  if (score >= 5.5) return "C-"
  if (score >= 5.0) return "D+"
  if (score >= 4.0) return "D"
  return "F"
}

function getScoreColor(score: number): string {
  if (score >= 8.5) return "border-green-500"
  if (score >= 7.0) return "border-blue-500"
  if (score >= 5.5) return "border-yellow-500"
  if (score >= 4.0) return "border-orange-500"
  return "border-red-500"
}

function calculateLanguageDistribution(fileAnalyses: Record<string, FileAnalysis>) {
  const languages = [
    { name: "Python", color: "#3572A5", count: 0 },
    { name: "JavaScript", color: "#f1e05a", count: 0 },
    { name: "TypeScript", color: "#2b7489", count: 0 },
    { name: "Other", color: "#8e8e8e", count: 0 },
  ]

  // Count files by extension
  Object.keys(fileAnalyses).forEach((filePath) => {
    const ext = filePath.split(".").pop()?.toLowerCase()
    if (ext === "py") languages[0].count++
    else if (ext === "js") languages[1].count++
    else if (ext === "ts" || ext === "tsx") languages[2].count++
    else languages[3].count++
  })

  const total = Object.keys(fileAnalyses).length
  if (total === 0) return languages.map((l) => ({ ...l, percentage: 0 }))

  // Calculate percentages
  return languages.map((lang) => ({
    ...lang,
    percentage: Math.round((lang.count / total) * 100) || 0,
  }))
}

function calculateIssuesBySeverity(fileAnalyses: Record<string, FileAnalysis>) {
  const issues = [
    { name: "Critical", color: "#ef4444", count: 0, percentage: 0 },
    { name: "Major", color: "#f97316", count: 0, percentage: 0 },
    { name: "Minor", color: "#eab308", count: 0, percentage: 0 },
  ]

  // This is a simplified calculation based on score ranges
  Object.values(fileAnalyses).forEach((analysis) => {
    Object.values(analysis.chunks).forEach((chunk) => {
      if (chunk.quality_score < 5) issues[0].count++
      else if (chunk.quality_score < 7) issues[1].count++
      else if (chunk.quality_score < 9) issues[2].count++
    })
  })

  const total = issues.reduce((sum, issue) => sum + issue.count, 0)
  if (total === 0) return issues

  // Calculate percentages
  return issues.map((issue) => ({
    ...issue,
    percentage: Math.round((issue.count / total) * 100) || 0,
  }))
}

import { Button } from "@/components/ui/button"
