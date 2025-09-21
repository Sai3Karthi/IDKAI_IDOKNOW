import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

export default function SummaryDisplay({ summary, originalText }) {
  const [copied, setCopied] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy summary:', err);
    }
  };

  const getCompressionRatio = () => {
    if (!originalText || !summary) return 0;
    return ((originalText.length - summary.length) / originalText.length * 100).toFixed(1);
  };

  const getWordCount = (text) => {
    return text.split(/\s+/).filter(Boolean).length;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-2 border-blue-500/30 rounded-lg bg-blue-500/5 backdrop-blur-sm"
    >
      <div className="flex items-center justify-between p-5 border-b border-blue-500/20">
        <h4 className="font-bold text-base flex items-center gap-3">
          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          AI Summary & Analysis
        </h4>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowComparison(!showComparison)}
            className="text-xs h-7 px-3 bg-blue-500/10 hover:bg-blue-500/20"
          >
            {showComparison ? 'Hide' : 'Compare'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={copyToClipboard}
            className="text-xs h-7 px-3 bg-blue-500/10 hover:bg-blue-500/20"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </Button>
        </div>
      </div>
      
      <div className="p-5">
        {showComparison ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h5 className="text-sm font-medium mb-2 text-muted-foreground">Original Text</h5>
              <div className="p-3 bg-background/40 rounded border text-sm max-h-48 overflow-y-auto scrollbar-thin">
                {originalText}
              </div>
              <div className="mt-2 text-xs text-muted-foreground">
                {originalText.length} characters • {getWordCount(originalText)} words
              </div>
            </div>
            <div>
              <h5 className="text-sm font-medium mb-2 text-muted-foreground">Generated Summary</h5>
              <div className="p-3 bg-primary/5 border border-primary/20 rounded text-sm max-h-48 overflow-y-auto scrollbar-thin">
                {summary}
              </div>
              <div className="mt-2 text-xs text-muted-foreground">
                {summary.length} characters • {getWordCount(summary)} words
              </div>
            </div>
          </div>
        ) : (
          <div>
            <div className="text-sm leading-relaxed text-foreground whitespace-pre-wrap mb-4">
              {summary}
            </div>
          </div>
        )}
        
        <div className="mt-4 pt-4 border-t border-border/20">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Summary Length:</span>
              <span className="font-medium">{summary.length} chars</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Word Count:</span>
              <span className="font-medium">{getWordCount(summary)} words</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Compression:</span>
              <span className="font-medium text-green-600 dark:text-green-400">
                {getCompressionRatio()}% reduction
              </span>
            </div>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-border/20">
          <div className="flex items-center justify-between text-xs text-muted-foreground/60">
            <span>AI-generated comprehensive summary</span>
            <div className="flex items-center gap-2">
              <div className="w-1 h-1 bg-green-500 rounded-full" />
              <span>Analysis complete</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}