'use client'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Crown, ArrowRight, FileText, Edit3, BarChart3 } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface PlanLimitationsNoticeProps {
  userRole: 'normal' | 'premium'
  quotesUsed: number
  className?: string
}

export function PlanLimitationsNotice({ userRole, quotesUsed, className }: PlanLimitationsNoticeProps) {
  const router = useRouter()

  if (userRole === 'premium') return null

  const quotesRemaining = 5 - quotesUsed
  const isNearLimit = quotesRemaining <= 1
  const isAtLimit = quotesRemaining <= 0

  return (
    <div className={className}>
      {(isNearLimit || isAtLimit) && (
        <Alert className="mb-3 border-orange-200 bg-orange-50">
          <AlertTriangle className="h-4 w-4 text-orange-600" />
          <AlertDescription className="flex items-center justify-between">
            <div className="flex-1">
              {isAtLimit ? (
                <div>
                  <p className="font-medium text-orange-900 mb-1">
                    Quote limit reached! You've used all 5 free quotes this month.
                  </p>
                  <div className="flex flex-wrap gap-2 text-sm text-orange-800">
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      Watermark on PDFs
                    </span>
                    <span className="flex items-center gap-1">
                      <Edit3 className="h-3 w-3" />
                      No quote editing
                    </span>
                    <span className="flex items-center gap-1">
                      <BarChart3 className="h-3 w-3" />
                      Basic analytics only
                    </span>
                  </div>
                </div>
              ) : (
                <div>
                  <p className="font-medium text-orange-900 mb-1">
                    Only {quotesRemaining} quote{quotesRemaining === 1 ? '' : 's'} remaining in your free plan.
                  </p>
                  <p className="text-sm text-orange-800">
                    Upgrade to Premium for unlimited quotes and advanced features.
                  </p>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 ml-4">
              <Badge variant="outline" className="text-orange-700 border-orange-300">
                {quotesUsed}/5 Used
              </Badge>
              <Button
                size="sm"
                onClick={() => router.push('/auth?upgrade=true')}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <Crown className="h-3 w-3 mr-1" />
                Upgrade
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="rounded-md border bg-white p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500">Current Plan</p>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-orange-300 text-orange-700 bg-orange-50">Free</Badge>
              <span className="text-xs text-gray-500">Normal user</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{quotesUsed}/5 Used</Badge>
            <Button
              size="sm"
              onClick={() => router.push('/auth?upgrade=true')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              <Crown className="h-4 w-4 mr-1" />
              Upgrade
            </Button>
          </div>
        </div>

        <div className="grid gap-2 text-sm">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5" />
            <div>
              <p className="font-medium text-gray-900">Limited to 5 quotes per month</p>
              <p className="text-gray-500">You have {quotesRemaining < 0 ? 0 : quotesRemaining} remaining this month.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-gray-700">
            <FileText className="h-4 w-4" />
            Watermark on all PDF exports
          </div>
          <div className="flex items-center gap-2 text-gray-700">
            <Edit3 className="h-4 w-4" />
            No quote editing capability
          </div>
          <div className="flex items-center gap-2 text-gray-700">
            <BarChart3 className="h-4 w-4" />
            Basic analytics only
          </div>
        </div>
      </div>
    </div>
  )
}