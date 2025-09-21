import React from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

export default function URLValidator({ 
  url, 
  setUrl, 
  onValidate, 
  onKeyPress, 
  isValidating, 
  error,
  disabled = false
}) {
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyPress={onKeyPress}
            placeholder="Enter URL to validate (e.g., https://example.com)"
            className={cn(
              "w-full px-3 py-2 rounded-md border bg-background/50 backdrop-blur-sm",
              "text-sm placeholder:text-muted-foreground",
              "focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary",
              "transition-all duration-200",
              error ? "border-destructive focus:ring-destructive/20 focus:border-destructive" : "border-border"
            )}
            disabled={isValidating || disabled}
          />
          {isValidating && (
            <motion.div
              className="absolute right-3 top-1/2 -translate-y-1/2"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
            </motion.div>
          )}
        </div>
        <Button
          onClick={onValidate}
          disabled={isValidating || !url.trim() || disabled}
          className="px-6"
        >
          {isValidating ? 'Validating...' : 'Validate'}
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
