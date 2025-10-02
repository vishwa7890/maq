"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Loader2, Sparkles, ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function PromptEnhancerPage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [context, setContext] = useState("");
  const [tone, setTone] = useState("Professional");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setGeneratedPrompt("");
    setSuggestions([]);

    try {
      const payload = {
        topic,
        context: context || undefined,
        tone: tone || undefined,
      };
      const result = await api.generateAnalysisPrompt(payload);
      setGeneratedPrompt(result.prompt ?? "");
      setSuggestions(result.suggestions ?? []);
    } catch (err: any) {
      const fallbackMessage = err?.message || "Unable to generate prompt. Please try again.";
      setError(fallbackMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Button variant="ghost" size="sm" className="mb-4" onClick={() => router.back()}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="h-7 w-7 text-blue-600" />
              Prompt Enhancer
            </h1>
            <p className="mt-2 text-slate-600 max-w-2xl">
              Craft analysis-grade prompts for your business questions. Provide a topic, optional background, and we will generate a refined AI prompt with structured guidance.
            </p>
          </div>
          <Link href="/chat">
            <Button variant="outline">Go to Chat</Button>
          </Link>
        </div>

        <div className="grid gap-6 md:grid-cols-[420px_1fr]">
          <Card className="shadow-lg border-0">
            <CardHeader>
              <CardTitle>Create AI Analysis Prompt</CardTitle>
              <CardDescription>
                Describe the business question you want to analyze. Add optional context and choose the tone you prefer.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="topic">Topic or question *</Label>
                  <Textarea
                    id="topic"
                    required
                    placeholder="e.g., Analyze the pricing strategy for our new SaaS product in the APAC market"
                    value={topic}
                    onChange={(event) => setTopic(event.target.value)}
                    className="min-h-[110px] resize-none"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="context">Additional business context</Label>
                  <Textarea
                    id="context"
                    placeholder="Key data points, assumptions, target audience, KPIs, competitive landscape..."
                    value={context}
                    onChange={(event) => setContext(event.target.value)}
                    className="min-h-[120px] resize-none"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tone">Desired tone</Label>
                  <Input
                    id="tone"
                    placeholder="Professional, concise, data-driven, strategic..."
                    value={tone}
                    onChange={(event) => setTone(event.target.value)}
                  />
                </div>

                {error && (
                  <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md px-3 py-2">
                    {error}
                  </div>
                )}

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating prompt...
                    </span>
                  ) : (
                    "Generate Analysis Prompt"
                  )}
                </Button>
              </form>
            </CardContent>
            <CardFooter className="text-xs text-slate-500">
              Outputs leverage your configured AI model key (OpenRouter/HF). Keep your API key current in backend `.env`.
            </CardFooter>
          </Card>

          <Card className="shadow-lg border border-blue-100 bg-white/80 backdrop-blur">
            <CardHeader>
              <CardTitle>Generated Prompt</CardTitle>
              <CardDescription>Copy directly into your preferred AI tool for a structured analysis workflow.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className={cn(
                  "rounded-lg border p-4 bg-slate-50 text-sm leading-6 whitespace-pre-wrap font-mono",
                  generatedPrompt ? "text-slate-800" : "text-slate-400"
                )}
              >
                {generatedPrompt || "Your enhanced prompt will appear here once generated."}
              </div>

              {suggestions.length > 0 && (
                <div className="space-y-2">
                  <Separator />
                  <h3 className="text-sm font-semibold text-slate-700">Recommended follow-ups</h3>
                  <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                    {suggestions.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
            <CardFooter className="flex justify-between text-xs text-slate-500">
              <span>Need to refine further? Adjust the context and regenerate.</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setGeneratedPrompt("");
                  setSuggestions([]);
                  setError(null);
                }}
              >
                Clear output
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}
