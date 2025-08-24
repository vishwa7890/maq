'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { MessageCircle, Plus, Send, Upload, Download, Edit3, BarChart3, User, Bot, FileText, Crown, Clipboard } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { ChatSidebar } from '@/components/chat-sidebar'
import { QuoteResponse } from '@/components/quote-response'
import { UserProfileButton } from '@/components/user-profile-button'
import { PlanLimitationsNotice } from '@/components/plan-limitations-notice'
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

  // Load html2pdf.js once into the current page
  const ensureHtml2Pdf = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      const anyWin = window as any
      if (anyWin.html2pdf) return resolve()
      const script = document.createElement('script')
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js'
      script.crossOrigin = 'anonymous'
      script.referrerPolicy = 'no-referrer'
      script.onload = () => resolve()
      script.onerror = () => reject(new Error('Failed to load html2pdf.js'))
      document.body.appendChild(script)
    })
  }

  // Auto-generate and download PDF using jsPDF (from html2pdf bundle) with fallback
  const downloadMessageAsPdf = async (msg: Message) => {
    // Prepare content outside try block to ensure it's available in catch block
    let contentHtml = convertMarkdownTablesToHtml(msg.content)
    if (!contentHtml || contentHtml.trim().length === 0) {
      const safe = mdEscapeHtml(msg.content || '')
      contentHtml = `<pre style="white-space:pre-wrap;word-wrap:break-word;font-size:12px;font-family:inherit;">${safe}</pre>`
    }

    try {
      // Ensure the PDF libraries are loaded
      await ensureHtml2Pdf()
      
      // Create a container for the PDF content
      const container = document.createElement('div')
      container.style.position = 'fixed'
      container.style.left = '0'
      container.style.top = '0'
      container.style.width = '794px' // A4 width at 96dpi
      container.style.padding = '24px'
      container.style.boxSizing = 'border-box'
      container.style.opacity = '0'
      container.style.pointerEvents = 'none'
      container.style.backgroundColor = '#ffffff'
      container.style.zIndex = '9999' // Ensure it's above other elements
      
      // Add watermark for free users
      const showWatermark = (user?.role === 'normal')
      const watermark = showWatermark
        ? `<div style="position:fixed;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;pointer-events:none;opacity:0.09;z-index:1;font-family:sans-serif;">
            <div style="transform:rotate(-30deg);font-size:84px;font-weight:800;color:#111827;letter-spacing:4px;">FREE PLAN</div>
          </div>`
        : ''
      
      // Set the container content
      container.innerHTML = `
        <div style="position:relative;width:100%;height:100%;">
          ${watermark}
          <div style="position:relative;z-index:2;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;color:#111827;">
            <h1 style="font-size:16px;margin:0 0 12px 0;font-weight:600;">Assistant Response</h1>
            <div style="font-size:14px;line-height:1.5;">
              ${contentHtml}
            </div>
          </div>
        </div>
      `
      
      // Add to document and wait for rendering
      document.body.appendChild(container)
      
      // Wait for any images to load and rendering to complete
      await new Promise<void>((resolve) => {
        // Check if there are any images in the content
        const images = container.getElementsByTagName('img')
        let imagesToLoad = images.length
        
        if (imagesToLoad === 0) {
          // No images, just wait for the next frame
          requestAnimationFrame(() => setTimeout(resolve, 100))
          return
        }
        
        // Wait for all images to load
        const onImageLoad = () => {
          imagesToLoad--
          if (imagesToLoad === 0) {
            // All images loaded, wait one more frame for good measure
            requestAnimationFrame(() => setTimeout(resolve, 100))
          }
        }
        
        // Set up load/error handlers for each image
        for (const img of Array.from(images)) {
          if (img.complete) {
            imagesToLoad--
          } else {
            img.addEventListener('load', onImageLoad)
            img.addEventListener('error', onImageLoad) // Also handle errors
          }
        }
        
        // In case all images are already loaded
        if (imagesToLoad === 0) {
          requestAnimationFrame(() => setTimeout(resolve, 100))
        }
      })
      
      // Get the PDF library
      const anyWin = window as any
      const jsPDFCtor = anyWin.jspdf?.jsPDF || anyWin.jsPDF || (anyWin.jspdf && anyWin.jspdf.jsPDF)
      
      // Try jsPDF with html2canvas first
      if (jsPDFCtor) {
        const doc = new jsPDFCtor({
          orientation: 'portrait',
          unit: 'mm',
          format: 'a4'
        })
        
        // Add HTML content with proper scaling and margins
        await doc.html(container, {
          x: 15,
          y: 15,
          width: 180, // 210mm - 15mm margins on each side
          windowWidth: 794, // Match the container width
          autoPaging: 'text',
          html2canvas: {
            scale: 2, // Higher scale for better quality
            useCORS: true,
            backgroundColor: '#ffffff',
            logging: true,
            scrollX: 0,
            scrollY: 0
          },
          callback: (doc: any) => {
            doc.save(`message-${msg.id}.pdf`)
            container.remove()
          },
        })
      } 
      // Fallback to html2pdf if available
      else if (anyWin.html2pdf) {
        const opt = {
          margin: 15,
          filename: `message-${msg.id}.pdf`,
          image: { 
            type: 'jpeg', 
            quality: 0.95 
          },
          html2canvas: { 
            scale: 2, 
            useCORS: true, 
            backgroundColor: '#ffffff',
            logging: true
          },
          jsPDF: { 
            unit: 'mm', 
            format: 'a4', 
            orientation: 'portrait' 
          }
        }
        
        await anyWin.html2pdf()
          .set(opt)
          .from(container)
          .save()
          .then(() => {
            container.remove()
          })
      } 
      // No PDF engine available
      else {
        throw new Error('No PDF generation library available')
      }
    } catch (e) {
      console.error('PDF generation error:', e)
      
      // Fallback to simple text-based PDF
      try {
        const anyWin = window as any
        const jsPDFCtor = anyWin.jspdf?.jsPDF || anyWin.jsPDF || (anyWin.jspdf && anyWin.jspdf.jsPDF)
        
        if (jsPDFCtor) {
          const doc = new jsPDFCtor({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
          })
          
          // Simple text rendering as fallback
          const safeText = (msg.content || '').replace(/\r/g, '')
          const lines = doc.splitTextToSize(safeText, 180) // 210mm - 15mm margins on each side
          
          // Set font and add header
          doc.setFont('helvetica', 'normal')
          doc.setFontSize(14)
          doc.text('Assistant Response', 15, 15)
          
          // Add content
          doc.setFontSize(11)
          doc.text(lines, 15, 25)
          
          // Add watermark for free users if needed
          if (user?.role === 'normal') {
            doc.setFontSize(60)
            doc.setTextColor(200, 200, 200)
            doc.setGState(new (doc as any).GState({ opacity: 0.2 }))
            doc.text('FREE PLAN', 30, 150, { angle: 45 })
          }
          
          // Save the PDF
          doc.save(`message-${msg.id}.pdf`)
          return
        }
      } catch (fallbackError) {
        console.error('Fallback PDF generation failed:', fallbackError)
      }
      
      // If all else fails, show an error to the user
      alert('Failed to generate PDF. Please try again or contact support.')
      
      // Robust fallback: open a printable HTML and trigger browser Print-to-PDF
      const printable = `<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>message-${msg.id}.pdf</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; padding: 24px; color: #111827; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { border: 1px solid #e5e7eb; padding: 6px 8px; text-align: left; }
    th { background: #f9fafb; }
    p { margin: 0 0 10px 0; }
    h1 { font-size: 16px; margin: 0 0 12px 0; }
    @page { margin: 12mm; }
    .wm { position: fixed; inset: 0; display:flex; align-items:center; justify-content:center; opacity:0.09; pointer-events:none; }
    .wm > div { transform: rotate(-30deg); font-size: 84px; font-weight: 800; color: #111827; letter-spacing: 4px; }
  </style>
  <script>
    window.addEventListener('load', () => {
      setTimeout(() => { try { window.print(); } catch(_){} }, 150);
    });
  </script>
  </head>
  <body>
    ${user?.role === 'normal' ? '<div class=\"wm\"><div>FREE PLAN</div></div>' : ''}
    <div style=\"position:relative; z-index:1;\">
      <h1>Assistant Response</h1>
      ${contentHtml}
    </div>
  </body>
  </html>`
      const w = window.open('', '_blank')
      if (!w) return
      w.document.open()
      w.document.write(printable)
      w.document.close()
    }
  }

  const openEdit = (msg: Message) => {
    setEditingMessageId(msg.id)
    setEditContent(msg.content)
    setIsEditOpen(true)
  }

  const copyMessage = async (msg: Message) => {
    try {
      await navigator.clipboard.writeText(msg.content || '')
      toast({ title: 'Copied', description: 'Assistant response copied to clipboard.' })
    } catch {
      toast({ variant: 'destructive', title: 'Copy failed', description: 'Could not copy to clipboard.' })
    }
  }

  const saveEdit = () => {
    if (!editingMessageId) return
    setMessages(prev => prev.map(m => m.id === editingMessageId ? { ...m, content: editContent } : m))
    setIsEditOpen(false)
    setEditingMessageId(null)
  }

  // Render assistant content with lightweight markdown table support
  const mdEscapeHtml = (s: string) => s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  const convertMarkdownTablesToHtml = (md: string): string => {
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
  }

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

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
      <ChatSidebar
        sessions={sessions}
        currentSession={currentSession}
        onSessionSelect={switchSession}
        onNewChat={() => createNewSession()}
        onFileUpload={handleFileUpload}
        user={user}
      />

      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-semibold">Lumina Quo Chat</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <Badge variant={user.role === 'premium' ? 'default' : 'secondary'}>
              {user.role === 'premium' ? (
                <>
                  <Crown className="h-3 w-3 mr-1" />
                  Premium
                </>
              ) : (
                `Normal (${(user.quotes_used ?? user.quotesUsed ?? 0)}/5 quotes used)`
              )}
            </Badge>
            
            <UserProfileButton user={user} />
            
            <Button
              variant="ghost"
              size="sm"
              onClick={async () => {
                try { await api.logout() } catch {}
                router.push('/auth')
              }}
            >
              Logout
            </Button>
          </div>
        </div>

        {/* Plan limitations (normal users) */}
        {user.role === 'normal' && (
          <div className="px-6 pt-4">
            <div className="max-w-4xl mx-auto">
              <PlanLimitationsNotice
                userRole={user.role}
                quotesUsed={(user.quotes_used ?? user.quotesUsed ?? 0)}
              />
            </div>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.type === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                )}
                
                <div className={`max-w-3xl ${message.type === 'user' ? 'order-first' : ''}`}>
                  <Card className={message.type === 'user' ? 'bg-blue-600 text-white rounded-xl' : 'bg-white rounded-xl shadow-sm border border-gray-100'}>
                    <CardContent className="p-4">
                      {message.type === 'assistant' ? (
                        <div
                          className="prose max-w-none text-sm"
                          dangerouslySetInnerHTML={{ __html: convertMarkdownTablesToHtml(message.content) }}
                        />
                      ) : (
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      )}
                      
                      {message.quote && (
                        <QuoteResponse 
                          quote={message.quote} 
                          userRole={user.role}
                          className="mt-4"
                        />
                      )}
                      {message.type === 'assistant' && (
                        <div className="flex gap-2 mt-3">
                          {user?.role === 'premium' && (
                            <Button size="sm" variant="outline" onClick={() => openEdit(message)}>
                              <Edit3 className="h-4 w-4 mr-1" /> Edit
                            </Button>
                          )}
                          <Button size="sm" variant="outline" onClick={() => copyMessage(message)} aria-label="Copy assistant message">
                            <Clipboard className="h-4 w-4 mr-1" /> Copy
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => downloadMessageAsPdf(message)}>
                            <Download className="h-4 w-4 mr-1" /> PDF
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                  
                  <div className={`text-xs text-gray-500 mt-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
                
                {message.type === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4 text-white" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <Card className="bg-white">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span>Generating quote...</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="bg-white border-t p-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Describe your project requirements for a quote..."
                  className="pr-12"
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <Button
                  size="sm"
                  className="absolute right-1 top-1"
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="relative">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Button variant="outline">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload PDF
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Edit Dialog */}
        <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Response</DialogTitle>
            </DialogHeader>
            <div className="space-y-2">
              <Textarea value={editContent} onChange={(e) => setEditContent(e.target.value)} rows={10} />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsEditOpen(false)}>Cancel</Button>
              <Button onClick={saveEdit}>Save</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
