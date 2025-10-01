'use client'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { MessageCircle, Plus, Upload, FileText, Crown, Clock, BarChart3, Menu, X } from 'lucide-react'
import { useState, useEffect } from 'react'

interface ChatSession {
  id: string
  name: string
  fileName?: string
  messages: any[]
  createdAt: Date
}

interface ChatSidebarProps {
  sessions: ChatSession[]
  currentSession: string | null
  onSessionSelect: (sessionId: string) => void
  onNewChat: () => void
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void
  user: any
  isMobile?: boolean
}

export function ChatSidebar({ 
  sessions, 
  currentSession, 
  onSessionSelect, 
  onNewChat, 
  onFileUpload,
  user,
  isMobile = false
}: ChatSidebarProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleSessionSelect = (sessionId: string) => {
    onSessionSelect(sessionId)
    if (isMobile) setIsOpen(false)
  }

  const handleNewChat = () => {
    onNewChat()
    if (isMobile) setIsOpen(false)
  }

  const SidebarContent = () => (
    <div className="w-80 lg:w-80 bg-white border-r flex flex-col h-full">
      {/* Header */}
      <div className="p-3 lg:p-4 border-b">
        <div className="flex items-center justify-between mb-3 lg:mb-4">
          <h2 className="font-semibold text-gray-900 text-sm lg:text-base">Chat Sessions</h2>
          {isMobile && (
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
              <X className="h-4 w-4" />
            </Button>
          )}
          {!isMobile && (
            <Badge variant={user.role === 'premium' ? 'default' : 'secondary'}>
              {user.role === 'premium' ? (
                <>
                  <Crown className="h-3 w-3 mr-1" />
                  Premium
                </>
              ) : (
                `${user.quotesUsed || 0}/5`
              )}
            </Badge>
          )}
        </div>
        
        <div className="space-y-2">
          <Button onClick={handleNewChat} className="w-full justify-start h-10 lg:h-9">
            <Plus className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sessions.map((session) => (
            <Button
              key={session.id}
              variant={currentSession === session.id ? 'secondary' : 'ghost'}
              className="w-full justify-start h-auto p-2 lg:p-3"
              onClick={() => handleSessionSelect(session.id)}
            >
              <div className="flex items-start gap-3 w-full">
                <div className="flex-shrink-0 mt-0.5">
                  {session.fileName ? (
                    <FileText className="h-4 w-4 text-blue-600" />
                  ) : (
                    <MessageCircle className="h-4 w-4 text-gray-600" />
                  )}
                </div>
                
                <div className="flex-1 text-left min-w-0">
                  <div className="font-medium text-xs lg:text-sm truncate">
                    {session.name}
                  </div>
                  
                  {session.fileName && (
                    <div className="text-xs text-gray-500 truncate">
                      {session.fileName}
                    </div>
                  )}
                  
                  <div className="flex items-center gap-1 text-xs text-gray-400 mt-1">
                    <Clock className="h-3 w-3" />
                    {session.createdAt.toLocaleDateString()}
                  </div>
                  
                  <div className="text-xs text-gray-500 mt-1">
                    {session.messages.length} messages
                  </div>
                </div>
              </div>
            </Button>
          ))}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-3 lg:p-4 border-t space-y-2">
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-start h-9"
          onClick={() => {
            if (user.role === 'premium') {
              window.location.href = '/dashboard'
            } else {
              window.location.href = '/dashboard/normal'
            }
            if (isMobile) setIsOpen(false)
          }}
        >
          <BarChart3 className="h-4 w-4 mr-2" />
          Dashboard
        </Button>
        
        <div className="text-xs text-gray-500 text-center">
          {user.role === 'normal' ? (
            <div>
              <p>Free Plan: {5 - (user.quotesUsed || 0)} quotes remaining</p>
              <p className="mt-1">Upgrade to Premium for unlimited access</p>
            </div>
          ) : (
            <p>Premium Plan: Unlimited quotes</p>
          )}
        </div>
      </div>
    </div>
  )

  // Handle mobile sidebar overlay
  useEffect(() => {
    if (isOpen && isMobile) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, isMobile])

  if (isMobile) {
    return (
      <>
        <Button 
          variant="ghost" 
          size="sm" 
          className="lg:hidden" 
          onClick={() => setIsOpen(true)}
        >
          <Menu className="h-4 w-4" />
        </Button>
        
        {/* Mobile Sidebar Overlay */}
        {isOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            {/* Backdrop */}
            <div 
              className="fixed inset-0 bg-black/50 backdrop-blur-sm" 
              onClick={() => setIsOpen(false)}
            />
            
            {/* Sidebar */}
            <div className="fixed left-0 top-0 h-full w-80 max-w-[85vw] bg-white shadow-xl transform transition-transform duration-300 ease-in-out">
              <SidebarContent />
            </div>
          </div>
        )}
      </>
    )
  }

  return <SidebarContent />
}

// Mobile Sidebar Trigger Component
export function MobileSidebarTrigger({ 
  sessions, 
  currentSession, 
  onSessionSelect, 
  onNewChat, 
  onFileUpload,
  user 
}: Omit<ChatSidebarProps, 'isMobile'>) {
  return (
    <ChatSidebar
      sessions={sessions}
      currentSession={currentSession}
      onSessionSelect={onSessionSelect}
      onNewChat={onNewChat}
      onFileUpload={onFileUpload}
      user={user}
      isMobile={true}
    />
  )
}
