import React from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

export default function ValidationHistory({ history, onSelectUrl, onClearHistory }) {
  if (history.length === 0) {
    return (
      <div className="border border-border/40 rounded-lg bg-background/20 backdrop-blur-sm p-4">
        <div className="text-center text-muted-foreground">
          <div className="text-2xl mb-2">•</div>
          <p className="text-sm">No validation history yet</p>
          <p className="text-xs opacity-60 mt-1">Your recent validations will appear here</p>
        </div>
      </div>
    );
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const truncateUrl = (url, maxLength = 40) => {
    if (url.length <= maxLength) return url;
    return url.slice(0, maxLength) + '...';
  };

  return (
    <div className="border border-border/40 rounded-lg bg-background/20 backdrop-blur-sm">
      <div className="flex items-center justify-between p-3 border-b border-border/40">
        <h4 className="font-medium text-sm flex items-center gap-2">
          <span className="text-lg">•</span>
          Validation History ({history.length})
        </h4>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearHistory}
          className="text-xs h-6 px-2 text-muted-foreground hover:text-destructive"
        >
          Clear All
        </Button>
      </div>
      
      <div className="max-h-40 overflow-y-auto custom-scrollbar">
        {history.map((entry, index) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              "flex items-center gap-3 p-3 hover:bg-background/40 cursor-pointer transition-colors",
              index !== history.length - 1 && "border-b border-border/20"
            )}
            onClick={() => onSelectUrl(entry.url)}
          >
            <div className={cn(
              "w-6 h-6 rounded-full flex items-center justify-center text-xs",
              entry.result.safe 
                ? "bg-green-500/20 text-green-600" 
                : "bg-red-500/20 text-red-600"
            )}>
              {entry.result.safe ? '✓' : '✗'}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate" title={entry.url}>
                {truncateUrl(entry.url)}
              </div>
              <div className="text-xs text-muted-foreground">
                {formatTime(entry.timestamp)} • {entry.result.safe ? 'Safe' : 'Unsafe'}
              </div>
            </div>
            
            <div className="text-xs text-muted-foreground">
              {entry.result.content ? `${entry.result.content.length} chars` : 'No content'}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
