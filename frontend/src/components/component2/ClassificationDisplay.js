import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

export default function ClassificationDisplay({ classification, hasSource }) {
  const categories = [
    { key: 'person', label: 'Personal', color: 'bg-blue-500', description: 'Personal attacks or bias' },
    { key: 'organization', label: 'Organizational', color: 'bg-purple-500', description: 'Institutional bias' },
    { key: 'social', label: 'Social', color: 'bg-green-500', description: 'Social/cultural bias' },
    { key: 'critical', label: 'Critical', color: 'bg-red-500', description: 'Critical misinformation' },
    { key: 'stem', label: 'STEM', color: 'bg-orange-500', description: 'Scientific/technical bias' }
  ];

  const maxScore = Math.max(...Object.values(classification));
  const totalScore = Object.values(classification).reduce((sum, val) => sum + val, 0);

  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="border-2 border-purple-500/30 rounded-lg bg-purple-500/5 backdrop-blur-sm p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-base flex items-center gap-3">
          <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
          Content Classification
        </h3>
        <div className="flex items-center gap-2">
          {hasSource && (
            <div className="px-3 py-1 bg-green-500/20 text-green-600 dark:text-green-400 rounded-full text-xs font-bold">
              ✓ Source Verified
            </div>
          )}
          <div className="text-xs text-muted-foreground">
            Total: {totalScore.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {categories.map((category, index) => {
          const score = classification[category.key];
          const percentage = totalScore > 0 ? (score / totalScore) * 100 : 0;
          const isHighest = score === maxScore && score > 0;

          return (
            <motion.div
              key={category.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "relative p-3 rounded-md border transition-all duration-200",
                isHighest 
                  ? "border-primary/40 bg-primary/5" 
                  : "border-border/20 bg-background/20"
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div 
                    className={cn("w-3 h-3 rounded-full", category.color)} 
                  />
                  <span className="font-medium text-sm">{category.label}</span>
                  {isHighest && score > 0 && (
                    <div className="w-1 h-1 bg-primary rounded-full animate-pulse" />
                  )}
                </div>
                <div className="text-sm font-mono">
                  {score.toFixed(3)}
                </div>
              </div>
              
              <div className="text-xs text-muted-foreground mb-2">
                {category.description}
              </div>
              
              <div className="relative h-2 bg-background/40 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ delay: index * 0.1 + 0.2, duration: 0.5 }}
                  className={cn("h-full rounded-full", category.color)}
                />
              </div>
              
              <div className="mt-1 text-xs text-muted-foreground text-right">
                {percentage.toFixed(1)}%
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-border/20">
        <div className="text-xs text-muted-foreground">
          Classification confidence based on content analysis
        </div>
      </div>
    </motion.div>
  );
}