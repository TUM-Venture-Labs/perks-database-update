import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Database, FileText, Activity, Clock, CheckCircle, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { formatRelativeTime } from "@/lib/utils"

// Mock data - replace with actual API calls
const dashboardStats = {
  perks: {
    total: 156,
    lastUpdated: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    successfulUpdates: 142,
    failedUpdates: 14
  },
  pitchdecks: {
    total: 89,
    pending: 23,
    analyzed: 66,
    approved: 18,
    rejected: 48
  }
}

const recentActivity = [
  {
    id: 1,
    type: "perk_update",
    title: "AWS Activate perk updated",
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    status: "success"
  },
  {
    id: 2,
    type: "pitchdeck_analysis",
    title: "TechStartup AI pitch analyzed",
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    status: "success"
  },
  {
    id: 3,
    type: "perk_update",
    title: "Google Cloud Credits update failed",
    timestamp: new Date(Date.now() - 1.5 * 60 * 60 * 1000),
    status: "error"
  }
]

export default function Dashboard() {
  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of your Venture Labs operations
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Perks</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.perks.total}</div>
            <p className="text-xs text-muted-foreground">
              Last updated {formatRelativeTime(dashboardStats.perks.lastUpdated)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pitchdeck Applications</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.pitchdecks.total}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardStats.pitchdecks.pending} pending analysis
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful Updates</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.perks.successfulUpdates}</div>
            <p className="text-xs text-muted-foreground">
              {((dashboardStats.perks.successfulUpdates / dashboardStats.perks.total) * 100).toFixed(1)}% success rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed Updates</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.perks.failedUpdates}</div>
            <p className="text-xs text-muted-foreground">
              Require attention
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and operations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Link href="/perks/add">
              <Button className="w-full justify-start" variant="outline">
                <Database className="w-4 h-4 mr-2" />
                Add New Perk
              </Button>
            </Link>
            <Button className="w-full justify-start" variant="outline">
              <Activity className="w-4 h-4 mr-2" />
              Run Perks Scraper
            </Button>
            <Link href="/pitchdecks">
              <Button className="w-full justify-start" variant="outline">
                <FileText className="w-4 h-4 mr-2" />
                Review Pitchdecks
              </Button>
            </Link>
            <Button className="w-full justify-start" variant="outline">
              <Clock className="w-4 h-4 mr-2" />
              Analyze Pending Applications
            </Button>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Latest updates and system activities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-center space-x-4 p-3 border rounded-lg">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{activity.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatRelativeTime(activity.timestamp)}
                    </p>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs ${
                    activity.status === 'success' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {activity.status}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Status */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>System Status</CardTitle>
          <CardDescription>
            Current status of system components
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium">Perks Scraper</p>
                  <p className="text-sm text-muted-foreground">Operational</p>
                </div>
              </div>
              <Button variant="outline" size="sm">
                View Logs
              </Button>
            </div>
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium">Pitchdeck Analyzer</p>
                  <p className="text-sm text-muted-foreground">Operational</p>
                </div>
              </div>
              <Button variant="outline" size="sm">
                View Logs
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
