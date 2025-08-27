'use client'

import { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { MessageCircle, Plus, Send, Upload, Download, Edit3, BarChart3, User, Bot, FileText, Crown, Clipboard } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { ChatSidebar, MobileSidebarTrigger } from '@/components/chat-sidebar'
import { UserProfileButton } from '@/components/user-profile-button'
import { PlanLimitationsNotice } from '@/components/plan-limitations-notice'
import { downloadMessageAsPdf } from '@/components/print-pdf'
import { api } from '@/lib/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/hooks/use-toast'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  quote?: any
}

interface ChatSession {
  id: string
  name: string
  fileName?: string
  messages: Message[]
  createdAt: Date
}

export default function ChatPage() {
  const [user, setUser] = useState<any>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSession, setCurrentSession] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { toast } = useToast()

  // --- Helpers & Handlers (top-level scope) ---

  const downloadText = (filename: string, text: string, type = 'text/plain') => {
    const blob = new Blob([text], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }


  const openEdit = useCallback((msg: Message) => {
    setEditingMessageId(msg.id)
    setEditContent(msg.content)
    setIsEditOpen(true)
  }, [])

  const copyMessage = async (msg: Message) => {
    try {
      await navigator.clipboard.writeText(msg.content || '')
      toast({ title: 'Copied', description: 'Assistant response copied to clipboard.' })
    } catch {
      toast({ variant: 'destructive', title: 'Copy failed', description: 'Could not copy to clipboard.' })
    }
  }

  const saveEdit = useCallback(() => {
    if (!editingMessageId) return
    setMessages(prev => prev.map(m => m.id === editingMessageId ? { ...m, content: editContent } : m))
    setIsEditOpen(false)
    setEditingMessageId(null)
  }, [editingMessageId, editContent])

  // Memoized markdown conversion for performance
  const mdEscapeHtml = useCallback((s: string) => s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;'), [])

  const convertMarkdownTablesToHtml = useCallback((md: string): string => {
    const lines = md.split(/\r?\n/)
    let i = 0
    const segments: string[] = []
    while (i < lines.length) {
      const line = lines[i]
      const next = lines[i + 1] || ''
      // Detect table header + separator line
      if (line.trim().startsWith('|') && /\|/.test(line) && /^\s*\|\s*:?[-]+.*\|\s*$/.test(next)) {
        const header = line
        i += 2
        const body: string[] = []
        while (i < lines.length && lines[i].trim().startsWith('|')) {
          body.push(lines[i])
          i++
        }
        const parseRow = (l: string) => l.trim().replace(/^\||\|$/g, '').split('|').map(c => mdEscapeHtml(c.trim()))
        const headerCells = parseRow(header)
        const bodyRows = body.map(parseRow)
        const th = headerCells.map(h => `<th style="border:1px solid #e5e7eb;padding:6px 8px;background:#f9fafb;text-align:left;">${h}</th>`).join('')
        const trs = bodyRows.map(r => `<tr>${r.map(c => `<td style="border:1px solid #e5e7eb;padding:6px 8px;vertical-align:top;">${c}</td>`).join('')}</tr>`).join('')
        segments.push(`<div style="overflow-x:auto;margin-top:8px;"><table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table></div>`)
        continue
      }
      // Fallback paragraph
      segments.push(`<p style="margin:0 0 10px 0;">${mdEscapeHtml(line)}</p>`)
      i++
    }
    return segments.join('\n')
  }, [mdEscapeHtml])

  useEffect(() => {
    const init = async () => {
      try {
        const me = await api.me()
        setUser(me)
      } catch {
        router.push('/auth')
        return
      }
      
      // Load sessions from backend
      try {
        const backendSessions = await api.listChatSessions()
        if (Array.isArray(backendSessions) && backendSessions.length > 0) {
          const mapped: ChatSession[] = backendSessions.map((s: any) => ({
            id: s.session_uuid || s.id,
            name: s.title || 'Chat',
            messages: [],
            createdAt: new Date(s.created_at || Date.now()),
          }))
          setSessions(mapped)
          // Pick first session and load messages
          const first = mapped[0]
          setCurrentSession(first.id)
          try {
            const msgs = await api.getSessionMessages(first.id)
            const mappedMsgs: Message[] = (Array.isArray(msgs) ? msgs : []).map((m: any, idx: number) => ({
              id: String(m.id ?? idx),
              type: (m.role === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
              content: m.content ?? '',
              timestamp: new Date(m.timestamp || m.created_at || Date.now()),
            }))
            setMessages(mappedMsgs)
          } catch {
            setMessages([])
          }
        } else {
          // Create a new backend session
          const created = await api.createChatSession({ title: 'New Chat' })
          const newSession: ChatSession = {
            id: created.id, // backend returns session_uuid as id in this route
            name: created.title || 'New Chat',
            messages: [{
              id: 'welcome',
              type: 'assistant',
              content: "Hi, I'm Lumina Quo - your business quotation expert!",
              timestamp: new Date()
            }],
            createdAt: new Date(created.created_at || Date.now()),
          }
          setSessions([newSession])
          setCurrentSession(newSession.id)
          setMessages(newSession.messages)
        }
      } catch (e) {
        // Fallback to a local welcome session if backend fails
        const welcomeSession: ChatSession = {
          id: 'welcome',
          name: 'Welcome Chat',
          messages: [{
            id: '1',
            type: 'assistant',
            content: "Hi, I'm QuestiMate - your business quotation expert!",
            timestamp: new Date()
          }],
          createdAt: new Date()
        }
        setSessions([welcomeSession])
        setCurrentSession('welcome')
        setMessages(welcomeSession.messages)
      }
    }
    init()
  }, [router])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const createNewSession = async (fileName?: string) => {
    try {
      const created = await api.createChatSession({ title: fileName ? `Chat - ${fileName}` : 'New Chat' })
      const newSession: ChatSession = {
        id: created.id, // session_uuid
        name: created.title || (fileName ? `Chat - ${fileName}` : `New Chat ${sessions.length}`),
        fileName,
        messages: [{
          id: Date.now().toString(),
          type: 'assistant',
          content: fileName 
            ? `I've received your file "${fileName}". Please tell me what kind of quote you need based on this document.`
            : "Hello! How can I help you create a quote today?",
          timestamp: new Date()
        }],
        createdAt: new Date(created.created_at || Date.now())
      }
      setSessions(prev => [newSession, ...prev])
      setCurrentSession(newSession.id)
      setMessages(newSession.messages)
    } catch (e) {
      // Fallback local if backend fails
      const localId = Date.now().toString()
      const newSession: ChatSession = {
        id: localId,
        name: fileName ? `Chat - ${fileName}` : `New Chat ${sessions.length}`,
        fileName,
        messages: [{
          id: Date.now().toString(),
          type: 'assistant',
          content: fileName 
            ? `I've received your file "${fileName}". Please tell me what kind of quote you need based on this document.`
            : "Hello! How can I help you create a quote today?",
          timestamp: new Date()
        }],
        createdAt: new Date()
      }
      setSessions(prev => [newSession, ...prev])
      setCurrentSession(newSession.id)
      setMessages(newSession.messages)
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type === 'application/pdf') {
      createNewSession(file.name)
    }
  }

  const sendChatToBackend = async (text: string, chatId?: string) => {
    const payload: any = { content: text }
    if (chatId) payload.chat_id = chatId
    const data = await api.sendChat(payload)
    return data
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !currentSession) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const data = await sendChatToBackend(userMessage.content, currentSession)
      const replyText: string = data?.content || 'No response.'
      const backendSessionId: string = data?.session_uuid || currentSession
      // If backend returned a different session id (newly created), switch to it
      if (backendSessionId !== currentSession) {
        setCurrentSession(backendSessionId)
      }
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: replyText,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      setSessions(prev => prev.map(session => 
        session.id === (backendSessionId || currentSession)
          ? { ...session, messages: [...session.messages, userMessage, assistantMessage] }
          : session
      ))
    } catch (e: any) {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: e?.message || 'Failed to send message',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const switchSession = async (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      setCurrentSession(sessionId)
      try {
        const msgs = await api.getSessionMessages(sessionId)
        const mappedMsgs: Message[] = (Array.isArray(msgs) ? msgs : []).map((m: any, idx: number) => ({
          id: String(m.id ?? idx),
          type: (m.role === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
          content: m.content ?? '',
          timestamp: new Date(m.timestamp || m.created_at || Date.now()),
        }))
        setMessages(mappedMsgs)
      } catch {
        setMessages(session.messages)
      }
    }
  }

  if (!user) return null

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile-optimized sidebar */}
      <div className="hidden lg:block">
        <ChatSidebar
          sessions={sessions}
          currentSession={currentSession}
          onSessionSelect={switchSession}
          onNewChat={() => createNewSession()}
          onFileUpload={handleFileUpload}
          user={user}
        />
      </div>

      <div className="flex-1 flex flex-col min-w-0">

        {/* Mobile header with menu */}
        <div className="lg:hidden bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MobileSidebarTrigger
              sessions={sessions}
              currentSession={currentSession}
              onSessionSelect={switchSession}
              onNewChat={() => createNewSession()}
              onFileUpload={handleFileUpload}
              user={user}
            />
            <h1 className="text-lg font-semibold text-gray-900">Chat</h1>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => createNewSession()}
            className="text-blue-600"
          >
            <Plus className="h-4 w-4 mr-1" />
            New
          </Button>
        </div>

        {/* Plan limitations (normal users) */}
        {user.role === 'normal' && (
          <div className="px-3 lg:px-6 pt-2 lg:pt-4">
            <div className="max-w-4xl mx-auto">
              <PlanLimitationsNotice
                userRole={user.role}
                quotesUsed={(user.quotes_used ?? user.quotesUsed ?? 0)}
              />
            </div>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 p-3 lg:p-6">
          <div className="max-w-4xl mx-auto space-y-4 lg:space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-2 lg:gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.type === 'assistant' && (
                  <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="h-3 w-3 lg:h-4 lg:w-4 text-white" />
                  </div>
                )}
                
                <div className={`max-w-[85%] lg:max-w-3xl ${message.type === 'user' ? 'order-first' : ''}`}>
                  <Card className={message.type === 'user' ? 'bg-blue-600 text-white rounded-2xl lg:rounded-xl' : 'bg-white rounded-2xl lg:rounded-xl shadow-sm border border-gray-100'}>
                    <CardContent className="p-3 lg:p-4">
                      {message.type === 'assistant' ? (
                        <div
                          className="prose max-w-none text-sm"
                          dangerouslySetInnerHTML={{ __html: convertMarkdownTablesToHtml(message.content) }}
                        />
                      ) : (
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      )}
                      
                      {message.type === 'assistant' && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          <Button size="sm" variant="outline" onClick={() => openEdit(message)} className="text-xs lg:text-sm">
                            <Edit3 className="h-3 w-3 lg:h-4 lg:w-4 mr-1" /> Edit
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => downloadMessageAsPdf(message, user)} className="text-xs lg:text-sm">
                            <Download className="h-3 w-3 lg:h-4 lg:w-4 mr-1" /> PDF
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                  
                  <div className={`text-xs text-gray-500 mt-1 px-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
                
                {message.type === 'user' && (
                  <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="h-3 w-3 lg:h-4 lg:w-4 text-white" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-2 lg:gap-4">
                <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-full bg-blue-600 flex items-center justify-center mt-1">
                  <Bot className="h-3 w-3 lg:h-4 lg:w-4 text-white" />
                </div>
                <Card className="bg-white rounded-2xl lg:rounded-xl">
                  <CardContent className="p-3 lg:p-4">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-3 w-3 lg:h-4 lg:w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm lg:text-base">Generating quote...</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="bg-white border-t p-3 lg:p-6 safe-area-inset-bottom">
          <div className="max-w-4xl mx-auto">
            <div className="flex flex-col lg:flex-row gap-3 lg:gap-4">
              <div className="flex-1 relative">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Describe your project requirements..."
                  className="pr-12 h-12 lg:h-10 text-base lg:text-sm"
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                />
                <Button
                  size="sm"
                  className="absolute right-1 top-1 h-10 lg:h-8"
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="relative lg:flex-shrink-0">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Button variant="outline" className="w-full lg:w-auto h-12 lg:h-10">
                  <Upload className="h-4 w-4 mr-2" />
                  <span className="lg:inline">Upload PDF</span>
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Edit Dialog */}
        <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit3 className="h-5 w-5" />
                Edit Assistant Response
              </DialogTitle>
            </DialogHeader>
            
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
              {/* Editor */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Edit Content</label>
                <Textarea 
                  value={editContent} 
                  onChange={(e) => setEditContent(e.target.value)} 
                  className="min-h-[300px] font-mono text-sm resize-none"
                  placeholder="Edit the assistant response content..."
                />
                <div className="text-xs text-gray-500">
                  {editContent.length} characters
                </div>
              </div>
              
              {/* Simplified Preview */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Preview</label>
                <div className="border rounded-md p-4 min-h-[300px] bg-gray-50 overflow-auto">
                  <div className="whitespace-pre-wrap text-sm font-mono">
                    {editContent || 'Preview will appear here...'}
                  </div>
                </div>
              </div>
            </div>
            
            <DialogFooter className="flex justify-between items-center pt-4 border-t">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Changes will be saved locally
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setIsEditOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={saveEdit} className="bg-blue-600 hover:bg-blue-700">
                  Save Changes
                </Button>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
