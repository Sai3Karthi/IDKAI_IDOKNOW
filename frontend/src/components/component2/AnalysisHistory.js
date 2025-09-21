import React from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

export default function AnalysisHistory({ history, onSelectText, onClearHistory }) {
  if (history.length === 0) {
    return (
      <div className="border border-border/40 rounded-lg bg-background/20 backdrop-blur-sm p-4">
        <div className="text-center text-muted-foreground">
          <div className="text-2xl mb-2">•</div>
          <p className="text-sm">No analysis history yet</p>
          <p className="text-xs opacity-60 mt-1">Your recent analyses will appear here</p>
        </div>
      </div>
    );
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const truncateText = (text, maxLength = 60) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-red-600 bg-red-500/20';
    if (score >= 60) return 'text-orange-600 bg-orange-500/20';
    if (score >= 40) return 'text-yellow-600 bg-yellow-500/20';
    if (score >= 20) return 'text-blue-600 bg-blue-500/20';
    return 'text-green-600 bg-green-500/20';
  };

  const getTopClassification = (classification) => {
    const entries = Object.entries(classification);
    const top = entries.reduce((max, [key, value]) => 
      value > max.value ? { key, value } : max, { key: '', value: 0 });
    
    const labels = {
      person: 'Personal',
      organization: 'Org',
      social: 'Social',
      critical: 'Critical',
      stem: 'STEM'
    };
    
    return labels[top.key] || 'Unknown';
  };

  return (
    <div className="border border-border/40 rounded-lg bg-background/20 backdrop-blur-sm">
      <div className="flex items-center justify-between p-3 border-b border-border/40">
        <h4 className="font-medium text-sm flex items-center gap-2">
          <span className="text-lg">•</span>
          Analysis History ({history.length})
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
      
      <div className="max-h-48 overflow-y-auto custom-scrollbar">
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
            onClick={() => onSelectText(entry.text)}
          >
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold",
              getScoreColor(entry.result.significance_score)
            )}>
              {entry.result.significance_score}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate" title={entry.text}>
                {truncateText(entry.text)}
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{formatTime(entry.timestamp)}</span>
                <span>•</span>
                <span>{getTopClassification(entry.result.classification)}</span>
                {entry.result.source && (
                  <>
                    <span>•</span>
                    <span className="text-green-600">Source</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="text-xs text-muted-foreground text-right">
              <div>{entry.text.length} chars</div>
              <div>{entry.text.split(/\s+/).filter(Boolean).length} words</div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}