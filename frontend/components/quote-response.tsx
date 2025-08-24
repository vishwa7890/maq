'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Download, Edit3, Save, X, FileText, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface QuoteItem {
  description: string
  quantity: number
  rate: number
  amount: number
}

interface Quote {
  id: string
  title?: string
  items: QuoteItem[]
  subtotal: number
  tax: number
  total: number
  terms?: string
  has_watermark?: boolean
  can_edit?: boolean
  created_at?: string
  validUntil?: Date
}

interface QuoteResponseProps {
  quote: Quote
  userRole: 'normal' | 'premium'
  className?: string
}

export function QuoteResponse({ quote, userRole, className }: QuoteResponseProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedItems, setEditedItems] = useState(quote.items)

  const handleEdit = () => {
    if (userRole !== 'premium') return
    setIsEditing(true)
  }

  const handleSave = () => {
    // Update quote with edited items
    setIsEditing(false)
    // Here you would typically save to backend
  }

  const handleCancel = () => {
    setEditedItems(quote.items)
    setIsEditing(false)
  }

  const updateItem = (index: number, field: keyof QuoteItem, value: string | number) => {
    const updated = [...editedItems]
    updated[index] = { ...updated[index], [field]: value }
    
    if (field === 'quantity' || field === 'rate') {
      updated[index].amount = updated[index].quantity * updated[index].rate
    }
    
    setEditedItems(updated)
  }

  const downloadPDF = () => {
    // Simulate PDF download
    const element = document.createElement('a')
    const file = new Blob(['Quote PDF content'], { type: 'application/pdf' })
    element.href = URL.createObjectURL(file)
    element.download = `quote-${quote.id}.pdf`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const subtotal = editedItems.reduce((sum, item) => sum + item.amount, 0)
  const tax = subtotal * 0.18 // 18% GST
  const total = subtotal + tax

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg">Professional Quote</CardTitle>
          {quote.title && (
            <p className="text-sm text-gray-600 mt-1">{quote.title}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {quote.validUntil && (
            <Badge variant="outline">
              Valid until {quote.validUntil.toLocaleDateString()}
            </Badge>
          )}
          
          {(quote.has_watermark || userRole === 'normal') && (
            <Badge variant="destructive" className="text-xs">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Watermarked
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Quote Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-200">
            <thead>
              <tr className="bg-gray-50">
                <th className="border border-gray-200 p-2 text-left">Description</th>
                <th className="border border-gray-200 p-2 text-center">Qty</th>
                <th className="border border-gray-200 p-2 text-right">Rate (₹)</th>
                <th className="border border-gray-200 p-2 text-right">Amount (₹)</th>
              </tr>
            </thead>
            <tbody>
              {(isEditing ? editedItems : quote.items).map((item, index) => (
                <tr key={index}>
                  <td className="border border-gray-200 p-2">
                    {isEditing ? (
                      <Input
                        value={item.description}
                        onChange={(e) => updateItem(index, 'description', e.target.value)}
                        className="h-8"
                      />
                    ) : (
                      item.description
                    )}
                  </td>
                  <td className="border border-gray-200 p-2 text-center">
                    {isEditing ? (
                      <Input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 0)}
                        className="h-8 w-16 text-center"
                      />
                    ) : (
                      item.quantity
                    )}
                  </td>
                  <td className="border border-gray-200 p-2 text-right">
                    {isEditing ? (
                      <Input
                        type="number"
                        value={item.rate}
                        onChange={(e) => updateItem(index, 'rate', parseInt(e.target.value) || 0)}
                        className="h-8 w-20 text-right"
                      />
                    ) : (
                      item.rate.toLocaleString()
                    )}
                  </td>
                  <td className="border border-gray-200 p-2 text-right font-medium">
                    ₹{item.amount.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={3} className="border border-gray-200 p-2 text-right font-medium">
                  Subtotal:
                </td>
                <td className="border border-gray-200 p-2 text-right font-medium">
                  ₹{subtotal.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td colSpan={3} className="border border-gray-200 p-2 text-right">
                  Tax (18%):
                </td>
                <td className="border border-gray-200 p-2 text-right">
                  ₹{tax.toLocaleString()}
                </td>
              </tr>
              <tr className="bg-blue-50">
                <td colSpan={3} className="border border-gray-200 p-2 text-right font-bold">
                  Total:
                </td>
                <td className="border border-gray-200 p-2 text-right font-bold text-blue-600">
                  ₹{total.toLocaleString()}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4">
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <Button size="sm" onClick={handleSave}>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </Button>
                <Button size="sm" variant="outline" onClick={handleCancel}>
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button size="sm" onClick={downloadPDF}>
                  <Download className="h-4 w-4 mr-2" />
                  Download PDF
                </Button>
                
                {userRole === 'premium' ? (
                  <Button size="sm" variant="outline" onClick={handleEdit}>
                    <Edit3 className="h-4 w-4 mr-2" />
                    Edit Quote
                  </Button>
                ) : (
                  <Button size="sm" variant="outline" disabled>
                    <Edit3 className="h-4 w-4 mr-2" />
                    Edit (Premium Only)
                  </Button>
                )}
              </>
            )}
          </div>

          {userRole === 'normal' && (
            <div className="text-xs text-red-600 flex items-center gap-1">
              <FileText className="h-3 w-3" />
              PDF will include watermark
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
