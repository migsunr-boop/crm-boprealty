"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Bell, Mail, HelpCircle, User, Settings, LogOut } from "lucide-react"

export default function TopNavbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 h-16 bg-gradient-to-r from-purple-600 to-blue-600 text-white z-50 shadow-lg">
      <div className="flex items-center justify-between h-full px-6">
        <div className="flex items-center gap-2">
          <div className="text-2xl">🏢</div>
          <span className="text-xl font-bold">BOP Realty</span>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="text-white hover:bg-white/10 relative">
            <Bell className="w-5 h-5" />
            <Badge className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center p-0">
              3
            </Badge>
          </Button>

          <Button variant="ghost" size="icon" className="text-white hover:bg-white/10">
            <Mail className="w-5 h-5" />
          </Button>

          <Button variant="ghost" size="icon" className="text-white hover:bg-white/10">
            <HelpCircle className="w-5 h-5" />
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="text-white hover:bg-white/10 gap-2">
                <User className="w-5 h-5" />
                <span>Admin User</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem>
                <User className="w-4 h-4 mr-2" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600">
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  )
}
