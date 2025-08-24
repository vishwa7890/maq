'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { useRouter } from 'next/navigation'
import { User, Settings, BarChart3, Crown, CreditCard, LogOut, Mail, Phone, Calendar } from 'lucide-react'

interface UserProfileButtonProps {
  user: {
    username: string
    email: string
    phone?: string
    role: 'normal' | 'premium'
    quotesUsed?: number
  }
}

export function UserProfileButton({ user }: UserProfileButtonProps) {
  const router = useRouter()

  const handleDashboard = () => {
    if (user.role === 'premium') {
      router.push('/dashboard')
    } else {
      router.push('/dashboard/normal')
    }
  }

  const handleUpgrade = () => {
    // Redirect to upgrade flow
    router.push('/?upgrade=true')
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    router.push('/')
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase() || name.slice(0, 2).toUpperCase()
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-10 w-10 rounded-full">
          <Avatar className="h-10 w-10">
            <AvatarFallback className="bg-blue-600 text-white">
              {getInitials(user.username)}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent className="w-80" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium leading-none">{user.username}</p>
              <Badge variant={user.role === 'premium' ? 'default' : 'secondary'}>
                {user.role === 'premium' ? (
                  <>
                    <Crown className="h-3 w-3 mr-1" />
                    Premium
                  </>
                ) : (
                  'Normal'
                )}
              </Badge>
            </div>
            
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Mail className="h-3 w-3" />
              {user.email}
            </div>
            
            {user.phone && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Phone className="h-3 w-3" />
                {user.phone}
              </div>
            )}
            
            {user.role === 'normal' && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <BarChart3 className="h-3 w-3" />
                {user.quotesUsed || 0}/5 quotes used
              </div>
            )}
          </div>
        </DropdownMenuLabel>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={handleDashboard}>
          <BarChart3 className="mr-2 h-4 w-4" />
          <span>Dashboard</span>
        </DropdownMenuItem>
        
        <DropdownMenuItem>
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        
        {user.role === 'normal' && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleUpgrade} className="text-blue-600">
              <Crown className="mr-2 h-4 w-4" />
              <span>Upgrade to Premium</span>
            </DropdownMenuItem>
          </>
        )}
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={handleLogout} className="text-red-600">
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
