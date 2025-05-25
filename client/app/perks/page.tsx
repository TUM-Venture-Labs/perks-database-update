"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  Plus, 
  Search, 
  Filter, 
  RefreshCw, 
  ExternalLink, 
  Clock, 
  AlertTriangle,
  CheckCircle
} from "lucide-react"
import Link from "next/link"
import { formatDate, formatRelativeTime, getStatusColor } from "@/lib/utils"

// Mock data - replace with actual API calls
const perksData = [
  {
    id: 1,
    name: "AWS Activate",
    category: "Cloud Credits",
    status: "active",
    lastUpdated: new Date(Date.now() - 2 * 60 * 60 * 1000),
    url: "https://aws.amazon.com/activate/",
    requirements: "Early-stage startup, funding required",
    value: "$100,000 credits",
    applicationWindow: "Year-round",
    availability: "Available"
  },
  {
    id: 2,
    name: "Google for Startups Cloud Program",
    category: "Cloud Credits",
    status: "active",
    lastUpdated: new Date(Date.now() - 4 * 60 * 60 * 1000),
    url: "https://cloud.google.com/startup",
    requirements: "Series A or earlier",
    value: "$200,000 credits",
    applicationWindow: "Year-round",
    availability: "Available"
  },
  {
    id: 3,
    name: "Microsoft for Startups",
    category: "Cloud Credits",
    status: "error",
    lastUpdated: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    url: "https://startups.microsoft.com/",
    requirements: "B2B focused, funding stage",
    value: "$150,000 credits",
    applicationWindow: "Ongoing",
    availability: "Limited"
  },
  {
    id: 4,
    name: "Stripe Atlas",
    category: "Legal/Finance",
    status: "active",
    lastUpdated: new Date(Date.now() - 6 * 60 * 60 * 1000),
    url: "https://stripe.com/atlas",
    requirements: "Delaware incorporation",
    value: "$5,000 credits",
    applicationWindow: "Year-round",
    availability: "Available"
  }
]

export default function PerksPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [categoryFilter, setCategoryFilter] = useState("all")

  const filteredPerks = perksData.filter(perk => {
    const matchesSearch = perk.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         perk.category.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || perk.status === statusFilter
    const matchesCategory = categoryFilter === "all" || perk.category === categoryFilter
    
    return matchesSearch && matchesStatus && matchesCategory
  })

  const handleRunScraper = async () => {
    // This would trigger the Python API endpoint
    console.log("Running scraper for all perks...")
  }

  const handleRefreshPerk = async (perkId: number) => {
    // This would trigger the Python API endpoint for a specific perk
    console.log(`Refreshing perk ${perkId}...`)
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Perks Database</h1>
            <p className="mt-2 text-gray-600">
              Manage and monitor startup perks and benefits
            </p>
          </div>
          <div className="flex space-x-3">
            <Button onClick={handleRunScraper} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Run Scraper
            </Button>
            <Link href="/perks/add">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add New Perk
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Perks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{perksData.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {perksData.filter(p => p.status === 'active').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {perksData.filter(p => p.status === 'error').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              {formatRelativeTime(new Date(Math.max(...perksData.map(p => p.lastUpdated.getTime()))))}
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
                  placeholder="Search perks..."
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
                <option value="active">Active</option>
                <option value="error">Error</option>
                <option value="pending">Pending</option>
              </select>
              <select
                className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="all">All Categories</option>
                <option value="Cloud Credits">Cloud Credits</option>
                <option value="Legal/Finance">Legal/Finance</option>
                <option value="Marketing">Marketing</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Perks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Perks ({filteredPerks.length})</CardTitle>
          <CardDescription>
            Manage your startup perks database
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-2">Perk Name</th>
                  <th className="text-left py-3 px-2">Category</th>
                  <th className="text-left py-3 px-2">Status</th>
                  <th className="text-left py-3 px-2">Value</th>
                  <th className="text-left py-3 px-2">Availability</th>
                  <th className="text-left py-3 px-2">Last Updated</th>
                  <th className="text-left py-3 px-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredPerks.map((perk) => (
                  <tr key={perk.id} className="border-b hover:bg-gray-50">
                    <td className="py-4 px-2">
                      <div className="flex items-center space-x-3">
                        <div>
                          <div className="font-medium">{perk.name}</div>
                          <a 
                            href={perk.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline flex items-center"
                          >
                            Visit <ExternalLink className="w-3 h-3 ml-1" />
                          </a>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">
                        {perk.category}
                      </span>
                    </td>
                    <td className="py-4 px-2">
                      <span className={`px-2 py-1 rounded-full text-xs flex items-center w-fit ${getStatusColor(perk.status)}`}>
                        {perk.status === 'active' && <CheckCircle className="w-3 h-3 mr-1" />}
                        {perk.status === 'error' && <AlertTriangle className="w-3 h-3 mr-1" />}
                        {perk.status === 'pending' && <Clock className="w-3 h-3 mr-1" />}
                        {perk.status}
                      </span>
                    </td>
                    <td className="py-4 px-2 font-medium">{perk.value}</td>
                    <td className="py-4 px-2">{perk.availability}</td>
                    <td className="py-4 px-2 text-sm text-gray-500">
                      {formatRelativeTime(perk.lastUpdated)}
                    </td>
                    <td className="py-4 px-2">
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefreshPerk(perk.id)}
                        >
                          <RefreshCw className="w-3 h-3" />
                        </Button>
                        <Link href={`/perks/${perk.id}`}>
                          <Button variant="outline" size="sm">
                            View
                          </Button>
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 