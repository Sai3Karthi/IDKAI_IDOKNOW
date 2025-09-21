import React from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

export default function TextAnalyzer({ 
  text, 
  setText, 
  onAnalyze, 
  onKeyPress, 
  isAnalyzing, 
  error,
  disabled = false,
  hasAttachedContent = false
}) {
  const placeholderText = hasAttachedContent 
    ? "Add additional context or analysis notes (optional)...\n\nThe attached URL content will be included automatically.\nPress Ctrl+Enter to analyze"
    : "Enter text to analyze for misinformation...\n\nExamples: News articles, social media posts, research claims\nPress Ctrl+Enter to analyze";

  return (
    <div className="space-y-3">
      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder={placeholderText}
          className={cn(
            "w-full px-3 py-3 rounded-md border bg-background/50 backdrop-blur-sm resize-none",
            "text-sm placeholder:text-muted-foreground min-h-[100px] max-h-[200px]",
            "focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary",
            "transition-all duration-200",
            error ? "border-destructive focus:ring-destructive/20 focus:border-destructive" : "border-border",
            disabled && "opacity-50 cursor-not-allowed"
          )}
          disabled={isAnalyzing || disabled}
          rows={4}
        />
        {isAnalyzing && (
          <motion.div
            className="absolute right-3 top-3"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
          </motion.div>
        )}
      </div>
      
      <div className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          {hasAttachedContent && (
            <span className="text-blue-600 mr-2">+ Attached content</span>
          )}
          {text.length} characters
          {text.length > 0 && (
            <span className="ml-2">
              • {text.split(/\s+/).filter(Boolean).length} words
            </span>
          )}
        </div>
        <Button
          onClick={onAnalyze}
          disabled={isAnalyzing || (!text.trim() && !hasAttachedContent) || disabled}
          className="px-6"
        >
          {isAnalyzing ? 'Analyzing...' : hasAttachedContent ? 'Analyze Content' : 'Analyze Text'}
        </Button>
      </div>
      
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md p-3"
        >
          <div className="flex items-center gap-2">
            <span className="text-destructive">!</span>
            {error}
          </div>
        </motion.div>
      )}
    </div>
  );
}