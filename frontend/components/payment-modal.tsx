'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CreditCard, Smartphone, Check } from 'lucide-react'

interface PaymentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  userEmail: string
}

export function PaymentModal({ isOpen, onClose, onSuccess, userEmail }: PaymentModalProps) {
  const [processing, setProcessing] = useState(false)

  const handlePayment = () => {
    setProcessing(true);
    // Open Razorpay payment link in a new tab
    window.open('https://rzp.io/rzp/XJAJXNa', '_blank');
    
    // Simulate payment success after a short delay
    setTimeout(() => {
      setProcessing(false);
      onSuccess();
    }, 1000);
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Premium Subscription
          </DialogTitle>
          <DialogDescription>
            Upgrade to Premium for unlimited quotes and advanced features
          </DialogDescription>
        </DialogHeader>

        <Card className="mb-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Premium Features</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-500" />
              <span>Unlimited quote generation</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-500" />
              <span>No watermark on PDFs</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-500" />
              <span>Edit quote functionality</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-500" />
              <span>Advanced dashboard & analytics</span>
            </div>
            <div className="text-lg font-bold text-blue-600 mt-3">₹99/month</div>
          </CardContent>
        </Card>

        <div className="text-center py-6">
          <CreditCard className="h-12 w-12 mx-auto mb-4 text-blue-500" />
          <p className="text-sm text-gray-600 mb-4">
            Secure Payment - ₹99/month
          </p>
          <Button 
            onClick={handlePayment}
            disabled={processing}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {processing ? 'Redirecting to Payment...' : 'Subscribe Now'}
          </Button>
        </div>

        <p className="text-xs text-gray-500 text-center">
          Secure payment powered by industry-standard encryption
        </p>
      </DialogContent>
    </Dialog>
  )
}
