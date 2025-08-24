'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CreditCard, Smartphone, Check } from 'lucide-react'

interface PaymentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  userEmail: string
}

export function PaymentModal({ isOpen, onClose, onSuccess, userEmail }: PaymentModalProps) {
  const [paymentMethod, setPaymentMethod] = useState('card')
  const [processing, setProcessing] = useState(false)
  const [cardData, setCardData] = useState({
    number: '',
    expiry: '',
    cvv: '',
    name: ''
  })

  const handlePayment = async () => {
    setProcessing(true)
    
    // Simulate payment processing
    setTimeout(() => {
      setProcessing(false)
      onSuccess()
    }, 2000)
  }

  const handleGooglePay = async () => {
    setProcessing(true)
    
    // Simulate Google Pay processing
    setTimeout(() => {
      setProcessing(false)
      onSuccess()
    }, 1500)
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
            <div className="text-lg font-bold text-blue-600 mt-3">₹999/month</div>
          </CardContent>
        </Card>

        <Tabs value={paymentMethod} onValueChange={setPaymentMethod}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="googlepay" className="flex items-center gap-2">
              <Smartphone className="h-4 w-4" />
              Google Pay
            </TabsTrigger>
            <TabsTrigger value="card" className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Card
            </TabsTrigger>
          </TabsList>

          <TabsContent value="googlepay" className="space-y-4">
            <div className="text-center py-6">
              <Smartphone className="h-12 w-12 mx-auto mb-4 text-blue-500" />
              <p className="text-sm text-gray-600 mb-4">
                Pay securely with Google Pay
              </p>
              <Button 
                onClick={handleGooglePay}
                disabled={processing}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {processing ? 'Processing...' : 'Pay with Google Pay'}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="card" className="space-y-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="card-name">Cardholder Name</Label>
                <Input
                  id="card-name"
                  placeholder="John Doe"
                  value={cardData.name}
                  onChange={(e) => setCardData(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="card-number">Card Number</Label>
                <Input
                  id="card-number"
                  placeholder="1234 5678 9012 3456"
                  value={cardData.number}
                  onChange={(e) => setCardData(prev => ({ ...prev, number: e.target.value }))}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="card-expiry">Expiry</Label>
                  <Input
                    id="card-expiry"
                    placeholder="MM/YY"
                    value={cardData.expiry}
                    onChange={(e) => setCardData(prev => ({ ...prev, expiry: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="card-cvv">CVV</Label>
                  <Input
                    id="card-cvv"
                    placeholder="123"
                    value={cardData.cvv}
                    onChange={(e) => setCardData(prev => ({ ...prev, cvv: e.target.value }))}
                  />
                </div>
              </div>

              <Button 
                onClick={handlePayment}
                disabled={processing}
                className="w-full"
              >
                {processing ? 'Processing Payment...' : 'Pay ₹999'}
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        <p className="text-xs text-gray-500 text-center">
          Secure payment powered by industry-standard encryption
        </p>
      </DialogContent>
    </Dialog>
  )
}
