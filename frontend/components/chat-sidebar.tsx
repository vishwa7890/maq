'use client'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { MessageCircle, Plus, Upload, FileText, Crown, Clock, BarChart3 } from 'lucide-react'

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
}

export function ChatSidebar({ 
  sessions, 
  currentSession, 
  onSessionSelect, 
  onNewChat, 
  onFileUpload,
  user 
}: ChatSidebarProps) {
  return (
    <div className="w-80 bg-white border-r flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Chat Sessions</h2>
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
        </div>
        
        <div className="space-y-2">
          <Button onClick={onNewChat} className="w-full justify-start">
            <Plus className="h-4 w-4 mr-2" />
            New Chat
          </Button>
          
          <div className="relative">
            <input
              type="file"
              accept=".pdf"
              onChange={onFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <Button variant="outline" className="w-full justify-start">
              <Upload className="h-4 w-4 mr-2" />
              Upload PDF
            </Button>
          </div>
        </div>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sessions.map((session) => (
            <Button
              key={session.id}
              variant={currentSession === session.id ? 'secondary' : 'ghost'}
              className="w-full justify-start h-auto p-3"
              onClick={() => onSessionSelect(session.id)}
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
                  <div className="font-medium text-sm truncate">
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
      <div className="p-4 border-t space-y-2">
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-start"
          onClick={() => {
            if (user.role === 'premium') {
              window.location.href = '/dashboard'
            } else {
              window.location.href = '/dashboard/normal'
            }
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
}
