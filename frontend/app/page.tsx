'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowRight, Sparkles, Quote, Shield, Zap, Lock, FileText, Check, Star } from 'lucide-react'
import { FeedbackForm } from '@/components/feedback-form'

import { Footer } from '@/components/footer';
import StatsSection from '@/components/stats-section';
import VisitorTracker from '@/components/VisitorTracker';
import VisitorCounter from '@/components/VisitorCounter';

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <VisitorTracker page="/" />
      <main className="relative flex-grow overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50">

      {/* Decorative background */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-[28rem] w-[28rem] rounded-full bg-blue-200/40 blur-3xl -z-10" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-[28rem] w-[28rem] rounded-full bg-pink-200/40 blur-3xl -z-10" />
      
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 pt-16 md:pt-24 pb-12 md:pb-16 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-white/80 px-3 sm:px-4 py-1.5 text-xs sm:text-sm text-blue-600 mb-4 sm:mb-6">
          <Sparkles className="h-3 w-3 sm:h-4 sm:w-4" /> 🚀 AI-Powered Quotation Generator
        </div>
        <h1 className="text-3xl sm:text-5xl md:text-7xl font-bold leading-tight mb-4 sm:mb-6 px-2">
          <span className="block sm:inline">Generate </span>
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Smart</span>
          <span className="block sm:inline"> </span>
          <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">Professional Quotations</span>
          <span className="block sm:inline"> </span>
          <span className="text-gray-900">in Seconds</span>
        </h1>
        <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-4xl mx-auto mb-6 sm:mb-8 px-4">
          Create beautiful, professional quotations with AI assistance. Export to PDF or Word, customize templates, and impress your clients – anytime, anywhere.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-8 px-4">
          <Link href="/auth" className="w-full sm:w-auto">
            <Button size="lg" className="w-full sm:w-auto px-8 py-3 text-base sm:text-lg">
              Generate Your First Quotation
            </Button>
          </Link>
          <a 
            href="https://lumina-quo.mindapt.in/demo" 
            target="_blank" 
            rel="noopener noreferrer"
            className="w-full sm:w-auto"
          >
            <Button 
              variant="outline" 
              size="lg" 
              className="w-full sm:w-auto px-8 py-3 text-base sm:text-lg border-2"
            >
              View Demo
            </Button>
          </a>
        </div>
        
        {/* Demo Card */}
        <div className="w-full max-w-md mx-auto bg-white rounded-2xl shadow-2xl p-4 sm:p-6 border">
          <div className="text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 text-green-600 mb-3">
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

      {/* Stats Section */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
        <StatsSection />
      </div>

      {/* Visitor Counter Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16 bg-white/50 backdrop-blur-sm rounded-3xl mx-4 mb-8">
        <VisitorCounter />
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
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
      <section id="pricing" className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <div className="text-center mb-8 sm:mb-12 px-2">
          <h2 className="text-3xl sm:text-4xl font-bold mb-3 sm:mb-4">Simple, Transparent Pricing</h2>
          <p className="text-base sm:text-lg text-gray-600 max-w-3xl mx-auto">Choose the plan that fits your needs. All plans include our core features with no hidden fees.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8 max-w-6xl mx-auto">
          {/* Generate Your First Quotation */}
          <Card className="hover:shadow-xl transition-shadow border-2 h-full flex flex-col">
            <CardHeader className="text-center pb-6 sm:pb-8">
              <CardTitle className="text-2xl">Generate Your First Quotation</CardTitle>
              <div className="text-4xl font-bold text-gray-900 mt-4">
                ₹0<span className="text-lg font-normal text-gray-600">/One-time</span>
              </div>
              <p className="text-gray-600 mt-2">Perfect for testing our platform</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>5 Free quotations</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>PDF export with watermark</span>
                </div>
              </div>
              <Link href="/auth" className="block">
                <Button className="w-full mt-6">Generate Your First Quotation</Button>
              </Link>
            </CardContent>
          </Card>

          {/* Pay Per Quote */}
          <Card className="hover:shadow-xl transition-shadow border-2">
            <CardHeader className="text-center pb-8">
              <CardTitle className="text-2xl">Professional Plan</CardTitle>
              <div className="text-4xl font-bold text-gray-900 mt-4">
                ₹99<span className="text-lg font-normal text-gray-600">/per quotation</span>
              </div>
              <p className="text-gray-600 mt-2">Ideal for professionals and businesses</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Premium professional quotations with detailed breakdowns</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Clean, watermark-free document exports</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>High-quality PDF exports with professional formatting</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Priority email & chat support</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Custom branding on all documents</span>
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
          <p className="mt-2">Have questions? <a href="mailto:vilaimathiai@gmail.com" className="text-blue-600 hover:underline">Contact our sales team</a></p>
        </div>
      </section>


      {/* Feedback Section */}
      <section id="feedback" className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">We'd Love Your Feedback</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Help us improve by sharing your thoughts and suggestions about our product.
            </p>
          </div>
          <div className="bg-white rounded-2xl shadow-lg p-8 max-w-2xl mx-auto">
            <FeedbackForm />
          </div>
        </div>
      </section>
      </main>
      <Footer />
    </div>
  )
}
