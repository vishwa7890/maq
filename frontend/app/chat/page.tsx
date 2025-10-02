'use client'

import { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { MessageCircle, Plus, Send, Upload, Download, Edit3, BarChart3, User, Bot, FileText, Crown, Clipboard, Sparkles, ArrowDown } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { ChatSidebar, MobileSidebarTrigger } from '@/components/chat-sidebar'
import { UserProfileButton } from '@/components/user-profile-button'
import { PlanLimitationsNotice } from '@/components/plan-limitations-notice'
import { downloadMessageAsPdf } from '@/components/print-pdf'
import { api } from '@/lib/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/hooks/use-toast'
import Image from 'next/image'

interface User {
  id?: number
  username?: string
  email?: string
  role: 'normal' | 'premium'
  quotes_used: number
  quotesUsed?: number
}

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
  const router = useRouter()
  const { toast } = useToast()
  const [user, setUser] = useState<User | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSession, setCurrentSession] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false)
  const [promptTopic, setPromptTopic] = useState('')
  const [promptTone, setPromptTone] = useState('Professional')
  const [promptResult, setPromptResult] = useState('')
  const [promptSuggestions, setPromptSuggestions] = useState<string[]>([])
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  const handleGeneratePrompt = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsGeneratingPrompt(true)
    setPromptResult('')
    setPromptSuggestions([])
    try {
      const payload = {
        topic: promptTopic,
        tone: promptTone || undefined,
      }
      const result = await api.generateAnalysisPrompt(payload)
      setPromptResult(result?.prompt ?? '')
      setPromptSuggestions(result?.suggestions ?? [])
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Prompt generation failed',
        description: error?.message || 'Unable to generate prompt. Please try again.',
      })
    } finally {
      setIsGeneratingPrompt(false)
    }
  }

  const applyGeneratedPrompt = () => {
    if (promptResult) {
      setInputValue(promptResult)
      setIsPromptModalOpen(false)
    }
  }

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
    const fetchData = async () => {
      try {
        const userData = await api.me()
        setUser(userData)
      } catch (error) {
        console.log('No active session, using anonymous mode')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [])

  useEffect(() => {
    const init = async () => {
      try {
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
                content: "Hi, I'm VilaiMathi AI - your business quotation expert!",
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
      } catch {
        router.push('/auth')
        return
      }
      
      // Ensure quotes_used is a number
      setUser((prev: any) => ({
        ...prev,
        quotes_used: Number(prev?.quotes_used || prev?.quotesUsed || 0)
      }))
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

  const fetchSessions = async () => {
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
        return mapped
      }
    } catch (error) {
      console.error('Error fetching sessions:', error)
    }
    return []
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !currentSession) return

    // If user is not logged in, redirect to auth page
    if (!user) {
      router.push('/auth?message=Please sign in to use the chat feature.')
      return
    }

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
      const response = await api.sendChat({
        content: inputValue,
        chat_id: currentSession || undefined
      })

      const assistantMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.content,
        timestamp: new Date(),
        quote: response.quote
      }

      setMessages(prev => [...prev, assistantMessage])

      // Update sessions if this is a new session
      if (response.session_id && !sessions.some(s => s.id === response.session_id)) {
        await fetchSessions()
        setCurrentSession(response.session_id)
      }
    } catch (e: any) {
      // Check if error is quota exceeded
      if (e?.response?.status === 429 || (e?.error === 'Quote limit reached')) {
        toast({
          variant: 'destructive',
          title: 'Quote limit reached',
          description: 'You\'ve used all 5 free quotes. Upgrade to Premium for unlimited quotes.'
        })
      } else {
        console.error('Error sending message:', e)
        toast({
          variant: 'destructive',
          title: 'Error',
          description: 'Failed to send message. Please try again.'
        })
      }
      
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
    <div className="flex h-screen bg-[#F5F5F5]">
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
            <h1 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Image
                src="/lumina_qou_png.png"
                alt="VilaiMathi AI"
                width={24}
                height={24}
                className="rounded"
              />
              Chat
            </h1>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => createNewSession()}
            className="text-[#4338CA] hover:text-[#362CA7]"
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
                  <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-full bg-[#4338CA] flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="h-3 w-3 lg:h-4 lg:w-4 text-white" />
                  </div>
                )}
                
                <div className={`max-w-[85%] lg:max-w-3xl ${message.type === 'user' ? 'order-first' : ''}`}>
                  <Card className={message.type === 'user' ? 'bg-[#17494D] text-white rounded-2xl lg:rounded-xl' : 'bg-white rounded-2xl lg:rounded-xl shadow-sm border border-[#17494D]/10'}>
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
                          <Button size="sm" variant="outline" onClick={() => openEdit(message)} className="text-xs lg:text-sm border-[#4338CA] text-[#4338CA] hover:bg-[#4338CA]/10">
                            <Edit3 className="h-3 w-3 lg:h-4 lg:w-4 mr-1" /> Edit
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => downloadMessageAsPdf(message, user)} className="text-xs lg:text-sm border-[#17494D] text-[#17494D] hover:bg-[#17494D]/10">
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
                  <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-full bg-[#17494D] flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="h-3 w-3 lg:h-4 lg:w-4 text-white" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-2 lg:gap-4">
                <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-full bg-[#4338CA] flex items-center justify-center mt-1">
                  <Bot className="h-3 w-3 lg:h-4 lg:w-4 text-white" />
                </div>
                <Card className="bg-white rounded-2xl lg:rounded-xl">
                  <CardContent className="p-3 lg:p-4">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-3 w-3 lg:h-4 lg:w-4 border-b-2 border-[#4338CA]"></div>
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
            <div className="flex justify-center">
              <div className="flex w-full max-w-3xl gap-2 items-center">
                <Input
                  value={inputValue}
                  onChange={e => setInputValue(e.target.value)}
                  onKeyDown={e => {
                    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  placeholder="Ask VilaiMathi AI for a business quote..."
                  className="flex-1"
                />
                <div className="flex items-center gap-2">
                  <Button onClick={handleSendMessage} disabled={isLoading} className="bg-[#4338CA] hover:bg-[#362CA7]">
                    {isLoading ? 'Sending...' : <Send className="h-4 w-4" />}
                  </Button>
                  <Button
                    type="button"
                    variant={user?.role === 'premium' ? 'default' : 'outline'}
                    className={`flex items-center gap-2 ${user?.role === 'premium' ? 'bg-[#17494D] hover:bg-[#12373A]' : 'border-[#4338CA] text-[#4338CA] hover:bg-[#4338CA]/10'}`}
                    disabled={user?.role !== 'premium'}
                    onClick={() => {
                      if (user?.role !== 'premium') {
                        toast({
                          title: 'Premium feature',
                          description: 'Upgrade to Premium to use the Prompt Booster.',
                          variant: 'destructive',
                        })
                        return
                      }
                      setPromptTopic('')
                      setPromptTone('Professional')
                      setPromptResult('')
                      setPromptSuggestions([])
                      setIsPromptModalOpen(true)
                    }}
                  >
                    <Sparkles className="h-4 w-4" />
                    Prompt Booster
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Edit Dialog */}
        <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit3 className="h-5 w-5" />
                Edit assistant response
              </DialogTitle>
              <DialogDescription>
                Make quick corrections to the assistant message. This won't send anything to the model.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <Textarea
                value={editContent}
                onChange={event => setEditContent(event.target.value)}
                className="min-h-[180px]"
              />
            </div>
            <DialogFooter className="flex justify-between">
              <Button variant="ghost" onClick={() => setIsEditOpen(false)}>
                Cancel
              </Button>
              <Button onClick={saveEdit}>
                Save Changes
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Prompt Enhancer Modal */}
        <Dialog open={isPromptModalOpen} onOpenChange={setIsPromptModalOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-[#4BB3FD]" />
                Prompt Booster
              </DialogTitle>
              <DialogDescription>
                Generate a deep-dive business analysis prompt, then insert it into the chat.
              </DialogDescription>
            </DialogHeader>
            <ScrollArea className="max-h-[70vh] pr-2">
              <div className="grid gap-6 md:grid-cols-[360px_1fr]">
                <form className="space-y-4" onSubmit={handleGeneratePrompt}>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground" htmlFor="prompt-topic">
                      Topic or question
                    </label>
                    <Textarea
                      id="prompt-topic"
                      required
                      value={promptTopic}
                      onChange={event => setPromptTopic(event.target.value)}
                      placeholder="e.g., Evaluate financial viability of launching in APAC"
                      className="min-h-[110px] resize-none"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground" htmlFor="prompt-tone">
                      Desired Tone
                    </label>
                    <Input
                      id="prompt-tone"
                      value={promptTone}
                      onChange={event => setPromptTone(event.target.value)}
                      placeholder="Professional, concise, data-driven..."
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={isGeneratingPrompt}>
                    {isGeneratingPrompt ? 'Generating...' : 'Generate Analysis Prompt'}
                  </Button>
                </form>
                <div className="space-y-4">
                  <div className="rounded-lg border border-[#17494D]/10 bg-[#F5F5F5] p-4 text-sm leading-6 whitespace-pre-wrap font-mono min-h-[260px] text-[#17494D]">
                    {promptResult || 'Generated prompt will appear here. Provide details and click generate.'}
                  </div>
                  {promptSuggestions.length > 0 && (
                    <div className="space-y-2">
                      <Separator />
                      <h3 className="text-sm font-semibold text-[#17494D]">Suggested follow-ups</h3>
                      <ul className="list-disc list-inside text-sm text-[#17494D]/80 space-y-1">
                        {promptSuggestions.map((item, index) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </ScrollArea>
            <DialogFooter>
              <div className="flex items-center justify-between w-full">
                <p className="text-xs text-muted-foreground">
                  Prompts use your configured AI model key. Update backend `.env` to rotate keys when needed.
                </p>
                <div className="flex gap-2">
                  <Button variant="ghost" onClick={() => setIsPromptModalOpen(false)}>
                    Close
                  </Button>
                  <Button onClick={applyGeneratedPrompt} disabled={!promptResult}>
                    Use in Chat
                  </Button>
                </div>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
