"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ChevronLeft, ChevronRight, Users, Handshake, Building, Flame, TrendingUp, Download, Eye } from "lucide-react"

interface Project {
  id: number
  name: string
  location: string
  bhk_options: string
  price_range: string
  image: string
  status: "featured" | "upcoming" | "active"
  description: string
}

const featuredProjects: Project[] = [
  {
    id: 1,
    name: "Skyline Residency",
    location: "Bandra West, Mumbai",
    bhk_options: "2, 3, 4 BHK",
    price_range: "₹2.5 - 4.2 Cr",
    image: "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&h=400&fit=crop&q=80",
    status: "featured",
    description: "Luxury apartments with modern amenities",
  },
  {
    id: 2,
    name: "Green Valley Homes",
    location: "Whitefield, Bangalore",
    bhk_options: "1, 2, 3 BHK",
    price_range: "₹85L - 1.8 Cr",
    image: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&h=400&fit=crop&q=80",
    status: "upcoming",
    description: "Eco-friendly residential complex",
  },
  {
    id: 3,
    name: "Marina Heights",
    location: "Marine Drive, Mumbai",
    bhk_options: "3, 4, 5 BHK",
    price_range: "₹5.2 - 8.5 Cr",
    image: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=400&fit=crop&q=80",
    status: "featured",
    description: "Premium sea-facing apartments",
  },
  {
    id: 4,
    name: "Tech Park Residences",
    location: "Gurgaon, Delhi NCR",
    bhk_options: "2, 3 BHK",
    price_range: "₹1.2 - 2.8 Cr",
    image: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&h=400&fit=crop&q=80",
    status: "active",
    description: "Modern living near IT hubs",
  },
]

export default function Dashboard() {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)

  // Auto-play carousel
  useEffect(() => {
    if (!isAutoPlaying) return

    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % featuredProjects.length)
    }, 5000)

    return () => clearInterval(interval)
  }, [isAutoPlaying])

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % featuredProjects.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + featuredProjects.length) % featuredProjects.length)
  }

  const downloadBrochure = (projectId: number) => {
    // Simulate download
    alert(`Downloading brochure for project ${projectId}...`)
  }

  const viewProjectDetails = (projectId: number) => {
    // Navigate to project details
    alert(`Opening details for project ${projectId}...`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Hero Carousel Section */}
      <div className="relative h-[500px] bg-gradient-to-r from-purple-600 to-blue-600 overflow-hidden rounded-b-3xl mb-8">
        <div
          className="flex transition-transform duration-700 ease-in-out h-full"
          style={{ transform: `translateX(-${currentSlide * 100}%)` }}
          onMouseEnter={() => setIsAutoPlaying(false)}
          onMouseLeave={() => setIsAutoPlaying(true)}
        >
          {featuredProjects.map((project, index) => (
            <div key={project.id} className="w-full flex-shrink-0 relative">
              <div className="absolute inset-0 bg-black/20 z-10" />
              <img
                src={project.image || "/placeholder.svg"}
                alt={project.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 z-20 flex items-center justify-center">
                <div className="text-center text-white p-8 max-w-2xl">
                  <Badge className="mb-4 bg-white/20 text-white border-white/30">
                    {project.status === "featured"
                      ? "Featured Project"
                      : project.status === "upcoming"
                        ? "New Launch"
                        : "Available Now"}
                  </Badge>
                  <h1 className="text-4xl font-bold mb-4">{project.name}</h1>
                  <p className="text-xl mb-2 flex items-center justify-center gap-2">
                    <span>📍</span> {project.location}
                  </p>
                  <p className="text-lg mb-6 opacity-90">{project.description}</p>
                  <div className="flex justify-center gap-4 mb-6">
                    <Badge variant="secondary" className="bg-white/20 text-white">
                      🏠 {project.bhk_options}
                    </Badge>
                    <Badge variant="secondary" className="bg-white/20 text-white">
                      💰 {project.price_range}
                    </Badge>
                  </div>
                  <div className="flex justify-center gap-4">
                    <Button
                      onClick={() => downloadBrochure(project.id)}
                      className="bg-white text-purple-600 hover:bg-white/90"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download Brochure
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => viewProjectDetails(project.id)}
                      className="border-white text-white hover:bg-white/10"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Navigation Arrows */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute left-4 top-1/2 -translate-y-1/2 z-30 bg-white/20 hover:bg-white/30 text-white"
          onClick={prevSlide}
        >
          <ChevronLeft className="w-6 h-6" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-4 top-1/2 -translate-y-1/2 z-30 bg-white/20 hover:bg-white/30 text-white"
          onClick={nextSlide}
        >
          <ChevronRight className="w-6 h-6" />
        </Button>

        {/* Indicators */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 flex gap-2">
          {featuredProjects.map((_, index) => (
            <button
              key={index}
              className={`w-3 h-3 rounded-full transition-all ${
                index === currentSlide ? "bg-white scale-125" : "bg-white/50"
              }`}
              onClick={() => setCurrentSlide(index)}
            />
          ))}
        </div>
      </div>

      {/* Analytics Cards */}
      <div className="container mx-auto px-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm font-medium">Total Leads</p>
                  <p className="text-3xl font-bold">247</p>
                  <div className="flex items-center mt-2 text-blue-100">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    <span className="text-sm">+12% from last month</span>
                  </div>
                </div>
                <Users className="w-12 h-12 text-blue-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm font-medium">Conversions</p>
                  <p className="text-3xl font-bold">89</p>
                  <div className="flex items-center mt-2 text-green-100">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    <span className="text-sm">+8% from last month</span>
                  </div>
                </div>
                <Handshake className="w-12 h-12 text-green-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm font-medium">Active Projects</p>
                  <p className="text-3xl font-bold">12</p>
                  <div className="flex items-center mt-2 text-purple-100">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    <span className="text-sm">+5% from last month</span>
                  </div>
                </div>
                <Building className="w-12 h-12 text-purple-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm font-medium">Hot Leads</p>
                  <p className="text-3xl font-bold">34</p>
                  <div className="flex items-center mt-2 text-orange-100">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    <span className="text-sm">+15% from last month</span>
                  </div>
                </div>
                <Flame className="w-12 h-12 text-orange-200" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Charts Section */}
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">📈 Lead Generation Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center text-gray-500">
                <p>Lead generation chart will be displayed here</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🥧 Lead Sources</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center text-gray-500">
                <p>Lead sources pie chart will be displayed here</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
