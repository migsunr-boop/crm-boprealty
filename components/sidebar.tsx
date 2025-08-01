"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Building,
  Users,
  BarChart3,
  DollarSign,
  Handshake,
  Calendar,
  CheckSquare,
  PieChart,
  UserCog,
} from "lucide-react"

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Find Projects", href: "/projects", icon: Building },
  { name: "Lead Management", href: "/leads", icon: Users },
  { name: "Member Management", href: "/members", icon: UserCog },
  { name: "Reports", href: "/reports", icon: BarChart3 },
  { name: "My Earnings", href: "/earnings", icon: DollarSign },
  { name: "Client Portal", href: "/clients", icon: Handshake },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "Task Manager", href: "/tasks", icon: CheckSquare },
  { name: "Advanced Analytics", href: "/analytics", icon: PieChart },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-white border-r border-gray-200 overflow-y-auto">
      <div className="p-4">
        <nav className="space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-purple-100 text-purple-700 border-l-4 border-purple-600"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
