"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Plus, Users, Shield, Edit, Trash2 } from "lucide-react"

interface Member {
  id: number
  name: string
  email: string
  role: "admin" | "manager" | "agent" | "viewer"
  permissions: string[]
  status: "active" | "inactive"
  joinedAt: string
}

const availablePermissions = [
  { id: "dashboard", label: "Dashboard", description: "View dashboard analytics" },
  { id: "leads", label: "Lead Management", description: "Manage leads and contacts" },
  { id: "projects", label: "Projects", description: "View and manage projects" },
  { id: "clients", label: "Client Portal", description: "Access client information" },
  { id: "reports", label: "Reports", description: "Generate and view reports" },
  { id: "earnings", label: "Earnings", description: "View earnings and commissions" },
  { id: "calendar", label: "Calendar", description: "Manage appointments and schedules" },
  { id: "tasks", label: "Task Manager", description: "Create and manage tasks" },
  { id: "analytics", label: "Advanced Analytics", description: "Access detailed analytics" },
  { id: "members", label: "Member Management", description: "Manage team members" },
]

const initialMembers: Member[] = [
  {
    id: 1,
    name: "Admin User",
    email: "admin@boprealty.com",
    role: "admin",
    permissions: availablePermissions.map((p) => p.id),
    status: "active",
    joinedAt: "2024-01-01",
  },
  {
    id: 2,
    name: "Sales Manager",
    email: "manager@boprealty.com",
    role: "manager",
    permissions: ["dashboard", "leads", "projects", "clients", "reports", "calendar", "tasks"],
    status: "active",
    joinedAt: "2024-01-05",
  },
]

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>(initialMembers)
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [editingMember, setEditingMember] = useState<Member | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    role: "",
    permissions: [] as string[],
    status: "active",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (editingMember) {
      // Update existing member
      setMembers(members.map((member) => (member.id === editingMember.id ? { ...member, ...formData } : member)))
      setEditingMember(null)
    } else {
      // Add new member
      const newMember: Member = {
        id: Date.now(),
        ...formData,
        joinedAt: new Date().toISOString().split("T")[0],
      } as Member
      setMembers([...members, newMember])
    }

    setFormData({
      name: "",
      email: "",
      role: "",
      permissions: [],
      status: "active",
    })
    setIsAddDialogOpen(false)
  }

  const handleEdit = (member: Member) => {
    setEditingMember(member)
    setFormData({
      name: member.name,
      email: member.email,
      role: member.role,
      permissions: member.permissions,
      status: member.status,
    })
    setIsAddDialogOpen(true)
  }

  const handleDelete = (memberId: number) => {
    if (confirm("Are you sure you want to remove this member?")) {
      setMembers(members.filter((member) => member.id !== memberId))
    }
  }

  const handlePermissionChange = (permissionId: string, checked: boolean) => {
    if (checked) {
      setFormData({
        ...formData,
        permissions: [...formData.permissions, permissionId],
      })
    } else {
      setFormData({
        ...formData,
        permissions: formData.permissions.filter((p) => p !== permissionId),
      })
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin":
        return "bg-red-500"
      case "manager":
        return "bg-blue-500"
      case "agent":
        return "bg-green-500"
      case "viewer":
        return "bg-gray-500"
      default:
        return "bg-gray-500"
    }
  }

  const getStatusColor = (status: string) => {
    return status === "active" ? "bg-green-500" : "bg-gray-500"
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Member Management</h1>
          <p className="text-gray-600">Manage team members and their permissions</p>
        </div>

        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Plus className="w-4 h-4 mr-2" />
              Add New Member
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingMember ? "Edit Member" : "Add New Member"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Full Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email Address *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="role">Role *</Label>
                  <Select value={formData.role} onValueChange={(value) => setFormData({ ...formData, role: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">👑 Admin</SelectItem>
                      <SelectItem value="manager">👔 Manager</SelectItem>
                      <SelectItem value="agent">🏠 Agent</SelectItem>
                      <SelectItem value="viewer">👁️ Viewer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="status">Status</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">✅ Active</SelectItem>
                      <SelectItem value="inactive">❌ Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="text-base font-semibold">Page Access Permissions</Label>
                <p className="text-sm text-gray-600 mb-4">Select which pages this member can access</p>
                <div className="grid grid-cols-2 gap-4 max-h-60 overflow-y-auto border rounded-lg p-4">
                  {availablePermissions.map((permission) => (
                    <div key={permission.id} className="flex items-start space-x-3">
                      <Checkbox
                        id={permission.id}
                        checked={formData.permissions.includes(permission.id)}
                        onCheckedChange={(checked) => handlePermissionChange(permission.id, checked as boolean)}
                      />
                      <div className="grid gap-1.5 leading-none">
                        <Label
                          htmlFor={permission.id}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          {permission.label}
                        </Label>
                        <p className="text-xs text-muted-foreground">{permission.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsAddDialogOpen(false)
                    setEditingMember(null)
                    setFormData({
                      name: "",
                      email: "",
                      role: "",
                      permissions: [],
                      status: "active",
                    })
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
                  {editingMember ? "Update Member" : "Add Member"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Members</p>
                <p className="text-3xl font-bold">{members.length}</p>
              </div>
              <Users className="w-12 h-12 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Members</p>
                <p className="text-3xl font-bold">{members.filter((m) => m.status === "active").length}</p>
              </div>
              <Shield className="w-12 h-12 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Admins</p>
                <p className="text-3xl font-bold">{members.filter((m) => m.role === "admin").length}</p>
              </div>
              <Users className="w-12 h-12 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Members Table */}
      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Member</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.map((member) => (
                <TableRow key={member.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{member.name}</div>
                      <div className="text-sm text-gray-500">{member.email}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={`${getRoleColor(member.role)} text-white`}>{member.role}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={`${getStatusColor(member.status)} text-white`}>{member.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {member.permissions.length} pages
                      <div className="text-xs text-gray-500">
                        {member.permissions
                          .slice(0, 3)
                          .map((p) => availablePermissions.find((ap) => ap.id === p)?.label)
                          .join(", ")}
                        {member.permissions.length > 3 && "..."}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{member.joinedAt}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => handleEdit(member)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDelete(member.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
