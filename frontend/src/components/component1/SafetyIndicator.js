import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

export default function SafetyIndicator({ safe, url }) {
  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={cn(
        "rounded-lg border-2 p-4",
        safe 
          ? "border-green-500/30 bg-green-500/10" 
          : "border-red-500/30 bg-red-500/10"
      )}
    >
      <div className="flex items-center gap-3">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
          className={cn(
            "w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold",
            safe ? "bg-green-500/20 text-green-600" : "bg-red-500/20 text-red-600"
          )}
        >
          {safe ? '✓' : '✗'}
        </motion.div>
        
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className={cn(
              "font-semibold",
              safe ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
            )}>
              {safe ? 'Safe URL' : 'Unsafe URL'}
            </h3>
            <span className={cn(
              "px-2 py-0.5 rounded-full text-xs font-medium",
              safe 
                ? "bg-green-500/20 text-green-600 dark:text-green-400" 
                : "bg-red-500/20 text-red-600 dark:text-red-400"
            )}>
              {safe ? 'SECURE' : 'BLOCKED'}
            </span>
          </div>
          
          <p className="text-sm text-muted-foreground mb-2">
            {safe 
              ? 'This URL has been verified as safe by Google Safe Browsing and VirusTotal.'
              : 'This URL has been flagged as potentially harmful and should be avoided.'
            }
          </p>
          
          <div className="text-xs text-muted-foreground/80 font-mono break-all">
            {url}
          </div>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-border/40">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Verified by:</span>
          <div className="flex gap-2">
            <span className="px-2 py-1 bg-background/50 rounded border border-border/40">
              Google Safe Browsing
            </span>
            <span className="px-2 py-1 bg-background/50 rounded border border-border/40">
              VirusTotal
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
