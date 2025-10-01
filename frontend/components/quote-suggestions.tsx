'use client';

import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Sparkles, Zap, ShieldCheck, CheckCircle, Download, Share2, Edit, X } from 'lucide-react';
import { Progress } from './ui/progress';
import { useToast } from './ui/use-toast';

type QuoteSuggestion = {
  id: string;
  content: string;
  confidence: number;
  features: string[];
  isPremium: boolean;
};

export function QuoteSuggestions({
  suggestions,
  onSelect,
  onInteract,
  isPremium = false,
  remainingQuotes = 0,
  maxQuotes = 5,
  onUpgrade,
}: {
  suggestions: QuoteSuggestion[];
  onSelect: (suggestion: QuoteSuggestion) => void;
  onInteract: (suggestionId: string, action: string) => void;
  isPremium: boolean;
  remainingQuotes?: number;
  maxQuotes?: number;
  onUpgrade: () => void;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [previewedId, setPreviewedId] = useState<string | null>(null);
  const { toast } = useToast();

  const handleAction = (suggestionId: string, action: string) => {
    if (action === 'select') {
      setSelectedId(suggestionId);
      onSelect(suggestions.find(s => s.id === suggestionId)!);
    } else {
      onInteract(suggestionId, action);
      
      if (action === 'download') {
        toast({
          title: 'Quote Downloaded',
          description: 'Your quote has been downloaded successfully!',
          action: <CheckCircle className="text-green-500" />,
        });
      }
    }
  };

  // Auto-select the first suggestion if none selected
  useEffect(() => {
    if (suggestions.length > 0 && !selectedId) {
      setSelectedId(suggestions[0].id);
    }
  }, [suggestions, selectedId]);

  if (suggestions.length === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-yellow-500" />
          Smart Quote Suggestions
        </h3>
        {!isPremium && (
          <div className="flex items-center gap-2">
            <Progress 
              value={(remainingQuotes / maxQuotes) * 100} 
              className="w-24 h-2"
            />
            <span className="text-sm text-muted-foreground">
              {remainingQuotes}/{maxQuotes} free quotes
            </span>
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-primary hover:bg-primary/10"
              onClick={onUpgrade}
            >
              <Zap className="h-4 w-4 mr-1" />
              Upgrade
            </Button>
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {suggestions.map((suggestion) => (
          <Card 
            key={suggestion.id}
            className={`relative overflow-hidden transition-all hover:shadow-md ${
              selectedId === suggestion.id 
                ? 'border-2 border-primary' 
                : 'border border-border/50 hover:border-border'
            }`}
            onMouseEnter={() => setPreviewedId(suggestion.id)}
            onMouseLeave={() => setPreviewedId(null)}
          >
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <CardTitle className="text-base font-medium line-clamp-2">
                  {suggestion.content.substring(0, 60)}...
                </CardTitle>
                <div className="flex gap-1">
                  {suggestion.isPremium && (
                    <div className="relative inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-amber-50 to-amber-100 text-amber-800 border border-amber-200 shadow-sm">
                      <div className="absolute inset-0 bg-gradient-to-r from-amber-200/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-full" />
                      <ShieldCheck className="h-3 w-3 mr-1.5 text-amber-600" />
                      <span className="relative font-medium">Premium</span>
                    </div>
                  )}
                  <div className="relative inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200 shadow-sm">
                    <div className="absolute inset-0 bg-gradient-to-r from-slate-100/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-full" />
                    <span className="relative font-medium">{Math.round(suggestion.confidence * 100)}% Match</span>
                  </div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="pt-0">
              <div className="flex flex-wrap gap-1.5 mb-3">
                {suggestion.features.map((feature) => (
                  <div 
                    key={feature}
                    className="relative inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-50/80 text-slate-600 border border-slate-200/80 hover:bg-slate-100/80 transition-colors cursor-default"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-slate-100/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-md" />
                    <span className="relative">{feature}</span>
                  </div>
                ))}
              </div>
              
              <div className="flex justify-between items-center">
                <Button 
                  size="sm" 
                  variant={selectedId === suggestion.id ? 'default' : 'outline'}
                  onClick={() => handleAction(suggestion.id, 'select')}
                  className="flex-1 mr-2"
                >
                  {selectedId === suggestion.id ? 'Selected' : 'Select'}
                </Button>
                
                <div className="flex gap-1">
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8"
                    onClick={() => handleAction(suggestion.id, 'download')}
                    disabled={!isPremium && remainingQuotes <= 0}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8"
                    onClick={() => handleAction(suggestion.id, 'share')}
                  >
                    <Share2 className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8"
                    onClick={() => handleAction(suggestion.id, 'edit')}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              {!isPremium && remainingQuotes <= 0 && (
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center flex-col p-4 text-center">
                  <Zap className="h-6 w-6 text-yellow-500 mb-2" />
                  <p className="text-sm font-medium mb-2">Upgrade to Premium</p>
                  <p className="text-xs text-muted-foreground mb-3">
                    You've used all your free quotes this month
                  </p>
                  <Button size="sm" onClick={onUpgrade}>
                    Unlock Unlimited Quotes
                  </Button>
                </div>
              )}
            </CardContent>
            
            {previewedId === suggestion.id && (
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-background border rounded-lg shadow-lg p-3 w-64 z-10">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-medium">Preview</span>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setPreviewedId(null);
                    }}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-4">
                  {suggestion.content}
                </p>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
