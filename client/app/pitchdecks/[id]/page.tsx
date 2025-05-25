"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  ArrowLeft,
  FileText, 
  ThumbsUp, 
  ThumbsDown,
  Download,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Star,
  MessageSquare,
  User,
  Clock
} from "lucide-react"
import Link from "next/link"
import { formatDate, formatRelativeTime } from "@/lib/utils"
import { useParams } from "next/navigation"

// Mock data - replace with actual API calls
const getApplicationData = (id: string) => {
  const applications = {
    "1": {
      id: 1,
      teamName: "TechFlow AI",
      companyName: "TechFlow Inc.",
      submissionDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
      status: "analyzed",
      aiScore: 85,
      humanReview: "pending",
      stage: "Series A",
      sector: "AI/ML",
      fundingAsked: "$2M",
      pitchDeckUrl: "/uploads/techflow-pitch.pdf",
      teamMembers: ["John Doe (CEO)", "Jane Smith (CTO)", "Mike Johnson (CPO)"],
      extractedFields: {
        problem: "Clear market problem identified: Manual data processing takes 80% of analyst time",
        solution: "AI-powered automation platform that reduces manual work by 90%",
        market: "$50B TAM in business automation, growing 15% annually",
        business_model: "SaaS B2B subscription with per-seat pricing",
        traction: "100+ customers, $500K ARR, 40% month-over-month growth",
        competition: "Clear competitive differentiation through proprietary AI models",
        financials: "Break-even projected in 18 months with current funding",
        team: "Strong technical team with relevant industry experience"
      },
      analysisResults: {
        requirements_match: {
          score: 90,
          details: "Meets all technical requirements for SW/AI program",
          criteria: [
            { name: "AI/Software Focus", met: true, note: "Core AI automation platform" },
            { name: "Early Stage", met: true, note: "Series A stage appropriate" },
            { name: "Scalable Business Model", met: true, note: "SaaS model with proven traction" },
            { name: "Technical Team", met: true, note: "Strong CTO with AI background" }
          ]
        },
        due_diligence: {
          score: 82,
          market_validation: "Strong market research with credible sources",
          financial_projections: "Conservative and realistic projections",
          team_assessment: "Experienced team with relevant backgrounds",
          risk_factors: ["Market competition", "Customer acquisition cost"],
          external_sources: [
            { source: "Crunchbase", info: "Company verified, funding rounds confirmed" },
            { source: "LinkedIn", info: "Team backgrounds validated" },
            { source: "Industry reports", info: "Market size data corroborated" }
          ]
        },
        overall_assessment: {
          strengths: [
            "Clear value proposition",
            "Strong technical execution",
            "Proven market traction",
            "Experienced team"
          ],
          weaknesses: [
            "Limited geographic presence",
            "Dependence on key customers",
            "Competitive market"
          ],
          recommendation: "Strong candidate for program acceptance",
          confidence: 85
        }
      },
      analysisStatus: "completed",
      comments: [
        {
          id: 1,
          author: "Sarah Wilson",
          role: "Program Manager",
          timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
          content: "Impressive AI implementation. The technical approach is solid and the market opportunity is significant."
        },
        {
          id: 2,
          author: "Dr. Michael Chen", 
          role: "Technical Advisor",
          timestamp: new Date(Date.now() - 30 * 60 * 1000),
          content: "Team has strong credentials. Recommend proceeding to technical interview stage."
        }
      ]
    }
  }
  
  return applications[id as keyof typeof applications] || null
}

export default function PitchdeckDetailPage() {
  const params = useParams()
  const application = getApplicationData(params.id as string)
  const [newComment, setNewComment] = useState("")
  const [reviewStatus, setReviewStatus] = useState(application?.humanReview || "pending")

  if (!application) {
    return (
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Application Not Found</h1>
          <Link href="/pitchdecks">
            <Button className="mt-4">Back to Applications</Button>
          </Link>
        </div>
      </div>
    )
  }

  const handleStatusChange = (status: string) => {
    setReviewStatus(status)
    // This would call your Python API to update the status
    console.log(`Updating application ${application.id} status to ${status}`)
  }

  const handleAddComment = () => {
    if (newComment.trim()) {
      // This would call your Python API to add the comment
      console.log(`Adding comment: ${newComment}`)
      setNewComment("")
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600"
    if (score >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getScoreIcon = (score: number) => {
    if (score >= 80) return <CheckCircle className="w-5 h-5" />
    if (score >= 60) return <AlertTriangle className="w-5 h-5" />
    return <XCircle className="w-5 h-5" />
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <Link href="/pitchdecks">
            <Button variant="outline" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Applications
            </Button>
          </Link>
        </div>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{application.teamName}</h1>
            <p className="text-lg text-gray-600">{application.companyName}</p>
            <div className="flex items-center space-x-4 mt-2">
              <span className="text-sm text-gray-500">
                Submitted {formatRelativeTime(application.submissionDate)}
              </span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                {application.sector}
              </span>
              <span className="text-sm font-medium">{application.stage}</span>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Download Pitch
            </Button>
            <Button variant="outline">
              <ExternalLink className="w-4 h-4 mr-2" />
              View Original
            </Button>
          </div>
        </div>
      </div>

      {/* AI Score and Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">AI Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`flex items-center space-x-2 ${getScoreColor(application.aiScore)}`}>
              {getScoreIcon(application.aiScore)}
              <span className="text-2xl font-bold">{application.aiScore}/100</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Funding Requested</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{application.fundingAsked}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Team Size</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{application.teamMembers.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Review Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-2">
              <Button 
                variant={reviewStatus === "approved" ? "default" : "outline"}
                size="sm"
                onClick={() => handleStatusChange("approved")}
                className="text-green-600"
              >
                <ThumbsUp className="w-3 h-3" />
              </Button>
              <Button 
                variant={reviewStatus === "rejected" ? "default" : "outline"}
                size="sm"
                onClick={() => handleStatusChange("rejected")}
                className="text-red-600"
              >
                <ThumbsDown className="w-3 h-3" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Extracted Information */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Extracted Information</CardTitle>
              <CardDescription>AI-extracted key fields from the pitch deck</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(application.extractedFields).map(([key, value]) => (
                  <div key={key} className="border-b pb-3 last:border-b-0">
                    <div className="font-medium text-sm text-gray-700 uppercase tracking-wide mb-1">
                      {key.replace('_', ' ')}
                    </div>
                    <div className="text-sm text-gray-900">{value}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
              <CardDescription>Key team members and their roles</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {application.teamMembers.map((member, index) => (
                  <div key={index} className="flex items-center space-x-3 p-2 border rounded">
                    <User className="w-4 h-4 text-gray-400" />
                    <span className="text-sm">{member}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Analysis Results */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Requirements Assessment</CardTitle>
              <CardDescription>
                Match against program criteria (Score: {application.analysisResults.requirements_match.score}/100)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {application.analysisResults.requirements_match.criteria.map((criterion, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex items-center space-x-3">
                      {criterion.met ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                      <div>
                        <div className="font-medium text-sm">{criterion.name}</div>
                        <div className="text-xs text-gray-500">{criterion.note}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Due Diligence Results</CardTitle>
              <CardDescription>
                External validation and research (Score: {application.analysisResults.due_diligence.score}/100)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="font-medium text-sm mb-2">External Sources Checked</div>
                  <div className="space-y-2">
                    {application.analysisResults.due_diligence.external_sources.map((source, index) => (
                      <div key={index} className="text-sm p-2 bg-gray-50 rounded">
                        <div className="font-medium">{source.source}</div>
                        <div className="text-gray-600">{source.info}</div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="font-medium text-sm mb-2">Risk Factors</div>
                  <div className="space-y-1">
                    {application.analysisResults.due_diligence.risk_factors.map((risk, index) => (
                      <div key={index} className="text-sm text-red-600">• {risk}</div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Overall Assessment</CardTitle>
              <CardDescription>
                AI recommendation and analysis summary
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="font-medium text-sm mb-2">Strengths</div>
                  <div className="space-y-1">
                    {application.analysisResults.overall_assessment.strengths.map((strength, index) => (
                      <div key={index} className="text-sm text-green-600">• {strength}</div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="font-medium text-sm mb-2">Areas for Improvement</div>
                  <div className="space-y-1">
                    {application.analysisResults.overall_assessment.weaknesses.map((weakness, index) => (
                      <div key={index} className="text-sm text-yellow-600">• {weakness}</div>
                    ))}
                  </div>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="font-medium text-sm text-blue-900 mb-1">Recommendation</div>
                  <div className="text-sm text-blue-800">
                    {application.analysisResults.overall_assessment.recommendation}
                  </div>
                  <div className="text-xs text-blue-600 mt-2">
                    Confidence: {application.analysisResults.overall_assessment.confidence}%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Comments Section */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Review Comments</CardTitle>
          <CardDescription>Team discussion and notes</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {application.comments.map((comment) => (
              <div key={comment.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-medium text-sm">{comment.author}</div>
                      <div className="text-xs text-gray-500">{comment.role}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400">
                    {formatRelativeTime(comment.timestamp)}
                  </div>
                </div>
                <div className="text-sm text-gray-700">{comment.content}</div>
              </div>
            ))}
            
            {/* Add Comment */}
            <div className="border-t pt-4">
              <div className="flex space-x-3">
                <div className="flex-1">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="w-full p-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                </div>
                <Button onClick={handleAddComment} disabled={!newComment.trim()}>
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Comment
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 