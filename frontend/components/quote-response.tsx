'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, Calendar, Clock, IndianRupee, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { format, parseISO, isValid } from 'date-fns'

interface QuotePhase {
  name: string
  deliverables: string[]
  timeline: string
  cost: number
}

type QuoteItem = {
  description: string
  quantity: number
  unit_price: number
  amount: number
}

interface Quote {
  id: string
  client_name: string
  project_name: string
  project_type: string
  project_scope: string
  estimated_hours: number
  hourly_rate: number
  start_date: string
  end_date: string
  phases: QuotePhase[]
  total: number
  payment_terms: string
  notes: string
  has_watermark?: boolean
  can_edit?: boolean
  created_at?: string
  validUntil?: string
  title?: string
  items?: Array<{
    description: string
    quantity: number
    unit_price: number
    amount: number
  }>
}

interface QuoteResponseProps {
  quote: Quote
  userRole: 'normal' | 'premium'
  className?: string
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return 'To be determined'
  try {
    const date = new Date(dateString)
    return isValid(date) ? format(date, 'MMM d, yyyy') : 'Invalid date'
  } catch (e) {
    return 'Invalid date'
  }
}

export function QuoteResponse({ quote, userRole, className }: QuoteResponseProps) {
  const [formattedDate, setFormattedDate] = useState('')
  const [editedItems, setEditedItems] = useState<QuoteItem[]>((quote.items ?? []) as QuoteItem[])

  useEffect(() => {
    if (quote.created_at) {
      setFormattedDate(formatDate(quote.created_at))
    }
  }, [quote.created_at])

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  // Placeholder: implement PDF download and editing when ready

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Professional Quote</h2>
          {quote.title && (
            <p className="text-sm text-gray-600 mt-1">{quote.title}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {quote.validUntil && (
            <Badge variant="outline">
              Valid until {formatDate(quote.validUntil)}
            </Badge>
          )}
          
          {(quote.has_watermark || userRole === 'normal') && (
            <Badge variant="destructive" className="text-xs">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Sample
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium mb-2">Project Details</h3>
            <div className="space-y-1 text-sm">
              <p><span className="font-medium">Client:</span> {quote.client_name || 'N/A'}</p>
              <p><span className="font-medium">Project:</span> {quote.project_name || 'N/A'}</p>
              <p><span className="font-medium">Type:</span> {quote.project_type || 'N/A'}</p>
              <p><span className="font-medium">Scope:</span> {quote.project_scope || 'N/A'}</p>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Estimate Summary</h3>
            <div className="bg-muted/50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-2">
                <span>Estimated Hours:</span>
                <span className="text-right">{quote.estimated_hours || 'N/A'}</span>
                
                <span>Hourly Rate:</span>
                <span className="text-right">
                  <IndianRupee className="inline h-3.5 w-3.5 mr-0.5" />
                  {quote.hourly_rate?.toLocaleString() || 'N/A'}
                </span>
                
                <span className="font-semibold">Total Estimate:</span>
                <span className="text-right font-bold">
                  <IndianRupee className="inline h-4 w-4 mr-0.5" />
                  {quote.total ? formatCurrency(quote.total) : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Project Timeline</h2>
          <div className="space-y-6">
            {quote.phases?.map((phase, idx) => (
              <div key={idx} className="border-l-2 border-primary pl-4 relative">
                <div className="absolute -left-2 top-0 w-3 h-3 rounded-full bg-primary"></div>
                <div className="bg-card p-4 rounded-lg shadow-sm">
                  <div className="flex justify-between items-start">
                    <h3 className="font-medium text-lg">{phase.name}</h3>
                    <div className="flex items-center text-sm text-muted-foreground">
                      <Clock className="h-4 w-4 mr-1" />
                      {phase.timeline}
                    </div>
                  </div>
                  <div className="mt-2">
                    <h4 className="font-medium text-sm mb-1">Deliverables:</h4>
                    <ul className="space-y-1 text-sm">
                      {phase.deliverables.map((item, i) => (
                        <li key={i} className="flex items-start">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mt-3 pt-3 border-t flex justify-end">
                    <span className="font-medium">
                      <IndianRupee className="inline h-4 w-4 mr-1" />
                      {phase.cost.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <div>
            <h2 className="text-xl font-semibold mb-3">Payment Terms</h2>
            <div className="space-y-2 text-sm">
              {quote.payment_terms ? (
                <p>{quote.payment_terms}</p>
              ) : (
                <>
                  <div className="flex items-center">
                    <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    <span>50% advance payment to begin work</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    <span>50% upon project completion</span>
                  </div>
                </>
              )}
            </div>
          </div>
          
          <div>
            <h2 className="text-xl font-semibold mb-3">Project Validity</h2>
            <div className="space-y-2 text-sm">
              <div className="flex items-center">
                <Calendar className="h-4 w-4 mr-2 text-muted-foreground flex-shrink-0" />
                <span>Start: {quote.start_date ? format(parseISO(quote.start_date), 'MMM d, yyyy') : 'To be determined'}</span>
              </div>
              <div className="flex items-center">
                <Calendar className="h-4 w-4 mr-2 text-muted-foreground flex-shrink-0" />
                <span>End: {quote.end_date ? format(parseISO(quote.end_date), 'MMM d, yyyy') : 'To be determined'}</span>
              </div>
              {quote.validUntil && (
                <div className="flex items-center text-amber-600">
                  <Clock className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span>Valid until: {format(parseISO(quote.validUntil), 'MMM d, yyyy')}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {quote.notes && (
          <div className="mt-6 p-4 bg-muted/30 rounded-md">
            <h3 className="font-medium mb-2">Additional Notes</h3>
            <p className="text-sm">{quote.notes}</p>
          </div>
        )}
      </CardContent>

      <CardFooter className="bg-muted/20 border-t py-4">
        <div className="w-full flex flex-col md:flex-row justify-between items-center text-sm text-muted-foreground">
          <div className="text-center md:text-left mb-2 md:mb-0">
            <p>Prepared by Your Company</p>
            <p>contact@yourcompany.com</p>
          </div>
          <div className="text-center">
            <p>Thank you for your business!</p>
            <p className="text-xs mt-1">Quote #{Math.floor(100000 + Math.random() * 900000)}</p>
            <p className="text-xs">Prepared on {formattedDate || 'N/A'}</p>
          </div>
        </div>
      </CardFooter>
    </Card>
  )
}
