'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Crown, AlertTriangle, ArrowRight, Check } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface UpgradePromptProps {
  quotesUsed: number
  quotesLimit: number
  className?: string
}

export function UpgradePrompt({ quotesUsed, quotesLimit, className }: UpgradePromptProps) {
  const router = useRouter()

  const handleUpgrade = () => {
    router.push('/auth?upgrade=true')
  }

  return (
    <Card className={`border-orange-200 bg-gradient-to-br from-orange-50 to-red-50 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-600" />
            <CardTitle className="text-lg text-orange-900">Quote Limit Reached</CardTitle>
          </div>
          <Badge variant="destructive">
            {quotesUsed}/{quotesLimit} Used
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <p className="text-orange-800">
          You've used all {quotesLimit} quotes in your free plan. Upgrade to Premium to continue generating unlimited professional quotes.
        </p>
        
        <div className="grid md:grid-cols-2 gap-4">
          {/* Current Plan */}
          <div className="p-4 bg-white/60 rounded-lg border border-orange-200">
            <h4 className="font-semibold text-gray-900 mb-2">Current Plan: Free</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                {quotesLimit} quotes per month
              </li>
              <li className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-orange-500" />
                Watermark on PDF exports
              </li>
              <li className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-orange-500" />
                No quote editing
              </li>
              <li className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-orange-500" />
                Basic analytics only
              </li>
            </ul>
          </div>
          
          {/* Premium Plan */}
          <div className="p-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <Crown className="h-4 w-4 text-blue-600" />
              Premium Plan
            </h4>
            <ul className="space-y-1 text-sm text-blue-800">
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                Unlimited quotes
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                No watermark on exports
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                Full quote editing capability
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                Advanced analytics & insights
              </li>
            </ul>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <Button 
            onClick={handleUpgrade}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            <Crown className="h-4 w-4 mr-2" />
            Upgrade to Premium
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
          <Button 
            variant="outline" 
            onClick={() => router.push('/dashboard')}
            className="flex-1"
          >
            View Dashboard
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}