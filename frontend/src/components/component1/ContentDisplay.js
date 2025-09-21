import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

export default function ContentDisplay({ content }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const maxPreviewLength = 200;
  const shouldTruncate = content.length > maxPreviewLength;
  const displayContent = isExpanded ? content : content.slice(0, maxPreviewLength);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy content:', err);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="border border-border/40 rounded-lg bg-background/30 backdrop-blur-sm"
    >
      <div className="flex items-center justify-between p-3 border-b border-border/40">
        <h4 className="font-medium text-sm flex items-center gap-2">
          <span className="text-lg">•</span>
          Scraped Content
        </h4>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={copyToClipboard}
            className="text-xs h-6 px-2"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </Button>
          {shouldTruncate && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs h-6 px-2"
            >
              {isExpanded ? 'Show Less' : 'Show More'}
            </Button>
          )}
        </div>
      </div>
      
      <div className="p-3">
        <div className={cn(
          "text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap",
          "max-h-64 overflow-y-auto scrollbar-thin"
        )}>
          {displayContent}
          {shouldTruncate && !isExpanded && (
            <span className="text-primary cursor-pointer ml-1" onClick={() => setIsExpanded(true)}>
              ...read more
            </span>
          )}
        </div>
        
        <div className="mt-3 pt-3 border-t border-border/20 flex items-center justify-between text-xs text-muted-foreground/60">
          <span>Content length: {content.length} characters</span>
          <span>Auto-extracted main content</span>
        </div>
      </div>
    </motion.div>
  );
}
