"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Plus, Search, Download, Eye, Edit, Upload } from "lucide-react"

interface Project {
  id: number
  name: string
  location: string
  bhk_options: string
  price_range: string
  image: string
  status: "featured" | "upcoming" | "active" | "sold_out"
  description: string
  developer: string
  amenities: string[]
  brochure?: string
  createdAt: string
}

const initialProjects: Project[] = [
  {
    id: 1,
    name: "Skyline Residency",
    location: "Bandra West, Mumbai",
    bhk_options: "2, 3, 4 BHK",
    price_range: "₹2.5 - 4.2 Cr",
    image: "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&h=400&fit=crop&q=80",
    status: "featured",
    description: "Luxury apartments with modern amenities and stunning city views",
    developer: "Prestige Group",
    amenities: ["Swimming Pool", "Gym", "Clubhouse", "Garden", "Security"],
    brochure: "skyline-brochure.pdf",
    createdAt: "2024-01-10",
  },
  {
    id: 2,
    name: "Green Valley Homes",
    location: "Whitefield, Bangalore",
    bhk_options: "1, 2, 3 BHK",
    price_range: "₹85L - 1.8 Cr",
    image: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&h=400&fit=crop&q=80",
    status: "upcoming",
    description: "Eco-friendly residential complex with green spaces",
    developer: "Brigade Group",
    amenities: ["Park", "Jogging Track", "Kids Play Area", "Solar Panels"],
    createdAt: "2024-01-08",
  },
]

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>(initialProjects)
  const [searchQuery, setSearchQuery] = useState("")
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    location: "",
    bhk_options: "",
    price_range: "",
    image: "",
    status: "",
    description: "",
    developer: "",
    amenities: [] as string[],
    brochure: "",
  })

  const filteredProjects = projects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.developer.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (editingProject) {
      // Update existing project
      setProjects(projects.map((project) => (project.id === editingProject.id ? { ...project, ...formData } : project)))
      setEditingProject(null)
    } else {
      // Add new project
      const newProject: Project = {
        id: Date.now(),
        ...formData,
        createdAt: new Date().toISOString().split("T")[0],
      } as Project
      setProjects([...projects, newProject])
    }

    setFormData({
      name: "",
      location: "",
      bhk_options: "",
      price_range: "",
      image: "",
      status: "",
      description: "",
      developer: "",
      amenities: [],
      brochure: "",
    })
    setIsAddDialogOpen(false)
  }

  const handleEdit = (project: Project) => {
    setEditingProject(project)
    setFormData({
      name: project.name,
      location: project.location,
      bhk_options: project.bhk_options,
      price_range: project.price_range,
      image: project.image,
      status: project.status,
      description: project.description,
      developer: project.developer,
      amenities: project.amenities,
      brochure: project.brochure || "",
    })
    setIsAddDialogOpen(true)
  }

  const handleAmenityChange = (amenity: string) => {
    if (formData.amenities.includes(amenity)) {
      setFormData({
        ...formData,
        amenities: formData.amenities.filter((a) => a !== amenity),
      })
    } else {
      setFormData({
        ...formData,
        amenities: [...formData.amenities, amenity],
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "featured":
        return "bg-purple-500"
      case "upcoming":
        return "bg-blue-500"
      case "active":
        return "bg-green-500"
      case "sold_out":
        return "bg-gray-500"
      default:
        return "bg-gray-500"
    }
  }

  const downloadBrochure = (project: Project) => {
    if (project.brochure) {
      alert(`Downloading brochure: ${project.brochure}`)
    } else {
      alert("No brochure available for this project")
    }
  }

  const commonAmenities = [
    "Swimming Pool",
    "Gym",
    "Clubhouse",
    "Garden",
    "Security",
    "Parking",
    "Kids Play Area",
    "Jogging Track",
    "Tennis Court",
    "Basketball Court",
    "Library",
    "Spa",
    "Yoga Room",
    "Party Hall",
    "Business Center",
  ]

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Project Management</h1>
          <p className="text-gray-600">Manage your real estate projects and listings</p>
        </div>

        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Plus className="w-4 h-4 mr-2" />
              Add New Project
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingProject ? "Edit Project" : "Add New Project"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Project Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="developer">Developer *</Label>
                  <Input
                    id="developer"
                    value={formData.developer}
                    onChange={(e) => setFormData({ ...formData, developer: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="location">Location *</Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="bhk_options">BHK Options *</Label>
                  <Input
                    id="bhk_options"
                    placeholder="e.g., 2, 3, 4 BHK"
                    value={formData.bhk_options}
                    onChange={(e) => setFormData({ ...formData, bhk_options: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="price_range">Price Range *</Label>
                  <Input
                    id="price_range"
                    placeholder="e.g., ₹2.5 - 4.2 Cr"
                    value={formData.price_range}
                    onChange={(e) => setFormData({ ...formData, price_range: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="status">Status *</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="featured">⭐ Featured</SelectItem>
                      <SelectItem value="upcoming">🚀 Upcoming</SelectItem>
                      <SelectItem value="active">✅ Active</SelectItem>
                      <SelectItem value="sold_out">❌ Sold Out</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="image">Project Image URL</Label>
                <Input
                  id="image"
                  type="url"
                  placeholder="https://example.com/image.jpg"
                  value={formData.image}
                  onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the project features and highlights..."
                  rows={3}
                />
              </div>

              <div>
                <Label className="text-base font-semibold">Amenities</Label>
                <p className="text-sm text-gray-600 mb-3">Select available amenities</p>
                <div className="grid grid-cols-3 gap-2 max-h-40 overflow-y-auto border rounded-lg p-4">
                  {commonAmenities.map((amenity) => (
                    <label key={amenity} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.amenities.includes(amenity)}
                        onChange={() => handleAmenityChange(amenity)}
                        className="rounded"
                      />
                      <span className="text-sm">{amenity}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <Label htmlFor="brochure">Brochure Upload</Label>
                <div className="flex items-center gap-4 mt-2">
                  <Input
                    id="brochure"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) {
                        setFormData({ ...formData, brochure: file.name })
                      }
                    }}
                    className="flex-1"
                  />
                  <Button type="button" variant="outline" size="sm">
                    <Upload className="w-4 h-4 mr-2" />
                    Upload
                  </Button>
                </div>
                {formData.brochure && <p className="text-sm text-green-600 mt-1">✅ {formData.brochure}</p>}
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsAddDialogOpen(false)
                    setEditingProject(null)
                    setFormData({
                      name: "",
                      location: "",
                      bhk_options: "",
                      price_range: "",
                      image: "",
                      status: "",
                      description: "",
                      developer: "",
                      amenities: [],
                      brochure: "",
                    })
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
                  {editingProject ? "Update Project" : "Add Project"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search projects by name, location, or developer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProjects.map((project) => (
          <Card key={project.id} className="overflow-hidden hover:shadow-lg transition-shadow">
            <div className="relative h-48">
              <img
                src={project.image || "/placeholder.svg"}
                alt={project.name}
                className="w-full h-full object-cover"
              />
              <Badge className={`absolute top-3 right-3 ${getStatusColor(project.status)} text-white`}>
                {project.status.replace("_", " ")}
              </Badge>
            </div>
            <CardContent className="p-4">
              <h3 className="font-bold text-lg mb-2">{project.name}</h3>
              <p className="text-gray-600 text-sm mb-2 flex items-center">📍 {project.location}</p>
              <p className="text-gray-600 text-sm mb-2">🏢 {project.developer}</p>
              <div className="flex justify-between items-center mb-3">
                <Badge variant="outline">🏠 {project.bhk_options}</Badge>
                <Badge variant="outline">💰 {project.price_range}</Badge>
              </div>
              <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.description}</p>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handleEdit(project)}>
                  <Edit className="w-4 h-4 mr-1" />
                  Edit
                </Button>
                <Button size="sm" variant="outline" onClick={() => downloadBrochure(project)}>
                  <Download className="w-4 h-4 mr-1" />
                  Brochure
                </Button>
                <Button size="sm" variant="outline">
                  <Eye className="w-4 h-4 mr-1" />
                  View
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-2">No projects found</div>
          <div className="text-sm text-gray-400">
            {searchQuery ? "Try adjusting your search criteria" : "Start by adding your first project"}
          </div>
        </div>
      )}
    </div>
  )
}
