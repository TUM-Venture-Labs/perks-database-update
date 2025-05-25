"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  FileText, 
  Search, 
  Filter, 
  Play, 
  Eye, 
  ThumbsUp, 
  ThumbsDown,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Star
} from "lucide-react"
import Link from "next/link"
import { formatDate, formatRelativeTime, getStatusColor } from "@/lib/utils"

// Mock data - replace with actual API calls
const applicationsData = [
  {
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
    extractedFields: {
      problem: "Clear market problem identified",
      solution: "AI-powered automation platform",
      market: "$50B TAM",
      business_model: "SaaS B2B",
      traction: "100+ customers, $500K ARR"
    },
    analysisStatus: "completed"
  },
  {
    id: 2,
    teamName: "GreenTech Solutions",
    companyName: "GreenTech Ltd.",
    submissionDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    status: "pending",
    aiScore: null,
    humanReview: "not_started",
    stage: "Seed",
    sector: "CleanTech",
    fundingAsked: "$500K",
    pitchDeckUrl: "/uploads/greentech-pitch.pdf",
    extractedFields: null,
    analysisStatus: "pending"
  },
  {
    id: 3,
    teamName: "FinanceBot",
    companyName: "FinanceBot GmbH",
    submissionDate: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    status: "approved",
    aiScore: 92,
    humanReview: "approved",
    stage: "Pre-Seed",
    sector: "FinTech",
    fundingAsked: "$1M",
    pitchDeckUrl: "/uploads/financebot-pitch.pdf",
    extractedFields: {
      problem: "Complex financial planning for SMEs",
      solution: "AI-driven financial advisor",
      market: "$20B TAM",
      business_model: "Subscription SaaS",
      traction: "50+ pilot customers"
    },
    analysisStatus: "completed"
  },
  {
    id: 4,
    teamName: "DataViz Pro",
    companyName: "DataViz Technologies",
    submissionDate: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000),
    status: "rejected",
    aiScore: 45,
    humanReview: "rejected",
    stage: "Series B",
    sector: "Enterprise Software",
    fundingAsked: "$10M",
    pitchDeckUrl: "/uploads/dataviz-pitch.pdf",
    extractedFields: {
      problem: "Unclear problem statement",
      solution: "Generic visualization tool",
      market: "No clear market size",
      business_model: "Unclear monetization",
      traction: "Limited traction shown"
    },
    analysisStatus: "completed"
  }
]

export default function PitchdecksPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sectorFilter, setSectorFilter] = useState("all")

  const filteredApplications = applicationsData.filter(app => {
    const matchesSearch = app.teamName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         app.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         app.sector.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || app.status === statusFilter
    const matchesSector = sectorFilter === "all" || app.sector === sectorFilter
    
    return matchesSearch && matchesStatus && matchesSector
  })

  const handleAnalyzeApplication = async (applicationId: number) => {
    // This would trigger the Python API endpoint for analysis
    console.log(`Analyzing application ${applicationId}...`)
  }

  const handleBulkAnalyze = async () => {
    const pendingApps = applicationsData.filter(app => app.status === 'pending')
    console.log(`Analyzing ${pendingApps.length} pending applications...`)
  }

  const getScoreColor = (score: number | null) => {
    if (!score) return "text-gray-400"
    if (score >= 80) return "text-green-600"
    if (score >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getScoreIcon = (score: number | null) => {
    if (!score) return <Clock className="w-4 h-4" />
    if (score >= 80) return <CheckCircle className="w-4 h-4" />
    if (score >= 60) return <AlertTriangle className="w-4 h-4" />
    return <XCircle className="w-4 h-4" />
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Pitchdeck Analyzer</h1>
            <p className="mt-2 text-gray-600">
              AI-powered application screening and analysis
            </p>
          </div>
          <div className="flex space-x-3">
            <Button onClick={handleBulkAnalyze} variant="outline">
              <Play className="w-4 h-4 mr-2" />
              Analyze Pending
            </Button>
            <Button>
              <FileText className="w-4 h-4 mr-2" />
              Upload Application
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{applicationsData.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {applicationsData.filter(a => a.status === 'pending').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Analyzed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {applicationsData.filter(a => a.status === 'analyzed').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {applicationsData.filter(a => a.status === 'approved').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {applicationsData.filter(a => a.status === 'rejected').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search applications..."
                  className="pl-10 pr-4 py-2 w-full border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="flex space-x-3">
              <select
                className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="analyzed">Analyzed</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
              <select
                className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={sectorFilter}
                onChange={(e) => setSectorFilter(e.target.value)}
              >
                <option value="all">All Sectors</option>
                <option value="AI/ML">AI/ML</option>
                <option value="FinTech">FinTech</option>
                <option value="CleanTech">CleanTech</option>
                <option value="Enterprise Software">Enterprise Software</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Applications Table */}
      <Card>
        <CardHeader>
          <CardTitle>Applications ({filteredApplications.length})</CardTitle>
          <CardDescription>
            Venture Labs application pipeline
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-2">Team/Company</th>
                  <th className="text-left py-3 px-2">Sector</th>
                  <th className="text-left py-3 px-2">Stage</th>
                  <th className="text-left py-3 px-2">Funding</th>
                  <th className="text-left py-3 px-2">AI Score</th>
                  <th className="text-left py-3 px-2">Status</th>
                  <th className="text-left py-3 px-2">Submitted</th>
                  <th className="text-left py-3 px-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredApplications.map((app) => (
                  <tr key={app.id} className="border-b hover:bg-gray-50">
                    <td className="py-4 px-2">
                      <div>
                        <div className="font-medium">{app.teamName}</div>
                        <div className="text-sm text-gray-500">{app.companyName}</div>
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                        {app.sector}
                      </span>
                    </td>
                    <td className="py-4 px-2">{app.stage}</td>
                    <td className="py-4 px-2 font-medium">{app.fundingAsked}</td>
                    <td className="py-4 px-2">
                      <div className={`flex items-center space-x-2 ${getScoreColor(app.aiScore)}`}>
                        {getScoreIcon(app.aiScore)}
                        <span className="font-medium">
                          {app.aiScore ? `${app.aiScore}/100` : 'Pending'}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(app.status)}`}>
                        {app.status}
                      </span>
                    </td>
                    <td className="py-4 px-2 text-sm text-gray-500">
                      {formatRelativeTime(app.submissionDate)}
                    </td>
                    <td className="py-4 px-2">
                      <div className="flex space-x-2">
                        {app.status === 'pending' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAnalyzeApplication(app.id)}
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                        )}
                        <Link href={`/pitchdecks/${app.id}`}>
                          <Button variant="outline" size="sm">
                            <Eye className="w-3 h-3" />
                          </Button>
                        </Link>
                        {app.status === 'analyzed' && (
                          <div className="flex space-x-1">
                            <Button variant="outline" size="sm" className="text-green-600">
                              <ThumbsUp className="w-3 h-3" />
                            </Button>
                            <Button variant="outline" size="sm" className="text-red-600">
                              <ThumbsDown className="w-3 h-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Success Rate by Sector</CardTitle>
            <CardDescription>Approval rates across different sectors</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {['AI/ML', 'FinTech', 'CleanTech', 'Enterprise Software'].map(sector => {
                const sectorApps = applicationsData.filter(app => app.sector === sector)
                const approved = sectorApps.filter(app => app.status === 'approved').length
                const rate = sectorApps.length > 0 ? (approved / sectorApps.length * 100).toFixed(1) : '0'
                return (
                  <div key={sector} className="flex justify-between items-center">
                    <span className="text-sm">{sector}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{width: `${rate}%`}}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{rate}%</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest application updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {applicationsData.slice(0, 4).map(app => (
                <div key={app.id} className="flex items-center space-x-3 p-2 border rounded">
                  <div className={`w-2 h-2 rounded-full ${
                    app.status === 'approved' ? 'bg-green-500' : 
                    app.status === 'rejected' ? 'bg-red-500' : 
                    app.status === 'analyzed' ? 'bg-blue-500' : 'bg-yellow-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{app.teamName}</p>
                    <p className="text-xs text-gray-500">
                      {app.status === 'approved' ? 'Approved for program' : 
                       app.status === 'rejected' ? 'Application rejected' :
                       app.status === 'analyzed' ? 'Analysis completed' : 'Submitted application'}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {formatRelativeTime(app.submissionDate)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 