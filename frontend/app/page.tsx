'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowRight, Sparkles, Quote, Shield, Zap, Lock, FileText, Check, Star } from 'lucide-react'

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50">

      {/* Decorative background */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-[28rem] w-[28rem] rounded-full bg-blue-200/40 blur-3xl -z-10" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-[28rem] w-[28rem] rounded-full bg-pink-200/40 blur-3xl -z-10" />
      
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-white/80 px-4 py-2 text-sm text-blue-600 mb-6">
          <Sparkles className="h-4 w-4" /> 🚀 AI-Powered Quotation Generator
        </div>
        <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
          Generate <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Smart</span><br />
          <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">Professional Quotations</span><br />
          <span className="text-gray-900">in Seconds</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-4xl mx-auto mb-8">
          Create beautiful, professional quotations with AI assistance. Export to PDF or Word, customize templates, and impress your clients – anytime, anywhere.
        </p>
        <div className="flex items-center justify-center gap-4 mb-8">
          <Link href="/auth">
            <Button size="lg" className="px-8 py-3 text-lg">Start Free Trial</Button>
          </Link>
          <Link href="/chat">
            <Button size="lg" variant="outline" className="px-8 py-3 text-lg">View Demo</Button>
          </Link>
        </div>
        
        {/* Demo Card */}
        <div className="max-w-md mx-auto bg-white rounded-2xl shadow-2xl p-6 border">
          <div className="text-left">
            <div className="flex items-center gap-2 text-green-600 mb-3">
              <Check className="h-5 w-5" />
              <span className="font-semibold">Quotation Generated Successfully ✨</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">QUOTATION #</span>
                <span className="font-mono">QT-2024-001</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Date:</span>
                <span>27/8/2025</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Client:</span>
                <span>Acme Corp</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Service:</span>
                <span>Website Development</span>
              </div>
              <div className="flex justify-between font-semibold text-lg">
                <span>Amount:</span>
                <span className="text-green-600">₹50,000 + GST</span>
              </div>
            </div>
            <div className="mt-4 p-3 bg-blue-50 rounded-lg text-center text-sm text-blue-700">
              Ready for PDF/Word export...
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <Card className="hover:shadow-xl transition-shadow border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <Zap className="h-6 w-6 text-yellow-600" />
              </div>
              <CardTitle className="text-lg">Lightning Fast</CardTitle>
            </CardHeader>
            <CardContent className="text-gray-600">
              Generate professional quotations in under 30 seconds
            </CardContent>
          </Card>
          <Card className="hover:shadow-xl transition-shadow border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Lock className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle className="text-lg">Secure & Reliable</CardTitle>
            </CardHeader>
            <CardContent className="text-gray-600">
              Bank-grade security with 99.9% uptime guarantee
            </CardContent>
          </Card>
          <Card className="hover:shadow-xl transition-shadow border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <CardTitle className="text-lg">Multiple Formats</CardTitle>
            </CardHeader>
            <CardContent className="text-gray-600">
              Export as PDF, Word, or share directly with clients
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
          <p className="text-xl text-gray-600">Choose the plan that fits your needs. All plans include our core features with no hidden fees.</p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {/* Free Trial */}
          <Card className="hover:shadow-xl transition-shadow border-2">
            <CardHeader className="text-center pb-8">
              <CardTitle className="text-2xl">Free Trial</CardTitle>
              <div className="text-4xl font-bold text-gray-900 mt-4">
                ₹0<span className="text-lg font-normal text-gray-600">/One-time</span>
              </div>
              <p className="text-gray-600 mt-2">Perfect for testing our platform</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>1 Free quotation</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Basic templates</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>PDF export (with watermark)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Word export (with watermark)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Email support</span>
                </div>
              </div>
              <Link href="/auth" className="block">
                <Button className="w-full mt-6">Start Free Trial</Button>
              </Link>
            </CardContent>
          </Card>

          {/* Pay Per Quote */}
          <Card className="hover:shadow-xl transition-shadow border-2">
            <CardHeader className="text-center pb-8">
              <CardTitle className="text-2xl">Pay Per Quote</CardTitle>
              <div className="text-4xl font-bold text-gray-900 mt-4">
                ₹99<span className="text-lg font-normal text-gray-600">/per quotation</span>
              </div>
              <p className="text-gray-600 mt-2">Great for occasional users</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Professional quotations</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>All premium templates</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Watermark-free exports</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>PDF & Word export</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Priority support</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Custom branding</span>
                </div>
              </div>
              <Button variant="outline" className="w-full mt-6">Buy Per Quote</Button>
            </CardContent>
          </Card>

          {/* Unlimited Annual */}
          <Card className="hover:shadow-xl transition-shadow border-2 border-blue-500 relative">
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <div className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold flex items-center gap-1">
                <Star className="h-4 w-4" />
                Most Popular
              </div>
            </div>
            <CardHeader className="text-center pb-8 pt-8">
              <CardTitle className="text-2xl"> Unlimited Annual</CardTitle>
              <div className="text-4xl font-bold text-gray-900 mt-4">
                ₹799<span className="text-lg font-normal text-gray-600">/per year</span>
              </div>
              <p className="text-gray-600 mt-2">Best value for businesses</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Unlimited quotations</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>All premium templates</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Watermark-free exports</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>PDF & Word export</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Priority support</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Custom branding</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Advanced analytics</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Team collaboration</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>API access</span>
                </div>
              </div>
              <Button className="w-full mt-6 bg-blue-600 hover:bg-blue-700">Comming Soon</Button>
            </CardContent>
          </Card>
        </div>
        
        <div className="text-center mt-8 text-gray-600">
          <p>All plans include 24/7 customer support and a 30-day money-back guarantee</p>
          <p className="mt-2">Have questions? <Link href="#" className="text-blue-600 hover:underline">Contact our sales team</Link></p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 text-center text-sm text-gray-500 bg-white/50">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded flex items-center justify-center">
              <span className="text-white font-bold text-xs">L</span>
            </div>
            <span className="font-semibold">Lumina Quo</span>
          </div>
          <div className="space-x-6">
            <Link href="#pricing" className="hover:text-gray-900">Pricing</Link>
            <Link href="#features" className="hover:text-gray-900">Features</Link>
            <Link href="/auth" className="hover:text-gray-900">Sign In</Link>
            <Link href="/auth" className="hover:text-gray-900">Get Started</Link>
          </div>
        </div>
      </footer>
    </main>
  )
}
