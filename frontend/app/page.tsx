'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowRight, Sparkles, Quote, Shield } from 'lucide-react'

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Decorative background */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-[28rem] w-[28rem] rounded-full bg-blue-200/40 blur-3xl -z-10" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-[28rem] w-[28rem] rounded-full bg-pink-200/40 blur-3xl -z-10" />
      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-white/80 px-3 py-1 text-sm text-blue-600">
          <Sparkles className="h-4 w-4" /> AI-powered quotes for your business
        </div>
        <h1 className="mt-4 text-4xl md:text-6xl font-bold leading-tight">
          <span className="bg-gradient-to-r from-blue-600 to-pink-600 bg-clip-text text-transparent">Lumina Quo</span>{' '}
          helps you generate accurate, beautiful quotes in seconds
        </h1>
        <p className="mt-4 text-gray-600 max-w-3xl mx-auto">
          Create professional quotations, estimate costs, and share with clients. Upgrade for unlimited quotes and premium features.
        </p>
        {/* Categories */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {['Web Design','Maintenance','Social Media','Branding','E‑commerce'].map((c) => (
            <span key={c} className="rounded-full border bg-white/70 px-3 py-1 text-xs text-gray-700">
              {c}
            </span>
          ))}
        </div>
        <div className="mt-8 flex items-center justify-center gap-4">
          <Link href="/auth">
            <Button className="px-6">Get Started <ArrowRight className="ml-2 h-4 w-4" /></Button>
          </Link>
          <Link href="/chat">
            <Button variant="secondary" className="px-6" >Open Chat</Button>
          </Link>
        </div>
        {/* Stats */}
        <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
          <span>5 free quotes</span>
          <span className="hidden sm:inline">•</span>
          <span>No credit card required</span>
          <span className="hidden sm:inline">•</span>
          <span>Premium: unlimited exports</span>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 pb-16 grid md:grid-cols-3 gap-6">
        <Card className="hover:shadow-xl transition-shadow">
          <CardHeader className="flex flex-row items-center gap-2">
            <Quote className="h-6 w-6 text-purple-600" />
            <CardTitle>Smart Quote Generation</CardTitle>
          </CardHeader>
          <CardContent className="text-gray-600">
            Turn plain requirements into itemized quotes with AI. Customize items, taxes, and terms.
          </CardContent>
        </Card>
        <Card className="hover:shadow-xl transition-shadow">
          <CardHeader className="flex flex-row items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            <CardTitle>Free and Premium</CardTitle>
          </CardHeader>
          <CardContent className="text-gray-600">
            Start free with 5 quotes. Go premium for unlimited quotes and no watermark exports.
          </CardContent>
        </Card>
        <Card className="hover:shadow-xl transition-shadow">
          <CardHeader className="flex flex-row items-center gap-2">
            <Sparkles className="h-6 w-6 text-pink-600" />
            <CardTitle>Share and Export</CardTitle>
          </CardHeader>
          <CardContent className="text-gray-600">
            Export as PDF/image and share with clients instantly from your dashboard.
          </CardContent>
        </Card>
      </section>

      {/* Examples */}
      <section className="max-w-7xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-semibold mb-6">Sample Quotes</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {["Website redesign for local bakery","Monthly social media management","Annual maintenance contract","Mobile app MVP scope","E-commerce setup & onboarding","Branding package"].map((title, i) => (
            <Card key={i} className="hover:-translate-y-0.5 transition-transform">
              <CardHeader>
                <CardTitle className="text-lg flex items-center"><Quote className="h-5 w-5 mr-2 text-gray-400" />{title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-600">
                Auto-generated line items, taxes, and terms. Edit before sending to client.
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 text-center text-sm text-gray-500">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
          <span>© {new Date().getFullYear()} QuestiMate</span>
          <div className="space-x-4">
            <Link href="/auth" className="hover:text-gray-900">Sign in</Link>
            <Link href="/chat" className="hover:text-gray-900">Try Chat</Link>
          </div>
        </div>
      </footer>
    </main>
  )
}
