import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

export default function SignificanceDisplay({ score }) {
  const getScoreLevel = (score) => {
    if (score >= 80) return { level: 'Critical', color: 'bg-red-500', textColor: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/30' };
    if (score >= 60) return { level: 'High', color: 'bg-orange-500', textColor: 'text-orange-600 dark:text-orange-400', bgColor: 'bg-orange-500/10', borderColor: 'border-orange-500/30' };
    if (score >= 40) return { level: 'Medium', color: 'bg-yellow-500', textColor: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-500/10', borderColor: 'border-yellow-500/30' };
    if (score >= 20) return { level: 'Low', color: 'bg-blue-500', textColor: 'text-blue-600 dark:text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/30' };
    return { level: 'Minimal', color: 'bg-green-500', textColor: 'text-green-600 dark:text-green-400', bgColor: 'bg-green-500/10', borderColor: 'border-green-500/30' };
  };

  const scoreInfo = getScoreLevel(score);
  const percentage = Math.min(score, 100);

  const getScoreDescription = (score) => {
    if (score >= 80) return 'Requires immediate attention and fact-checking';
    if (score >= 60) return 'Significant concerns identified, review recommended';
    if (score >= 40) return 'Moderate risk detected, caution advised';
    if (score >= 20) return 'Low risk, minor concerns identified';
    return 'Content appears reliable with minimal risk';
  };

  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={cn(
        "border-2 rounded-lg bg-background/50 backdrop-blur-sm p-5",
        scoreInfo.borderColor,
        score >= 60 && "ring-2 ring-offset-2 ring-opacity-50",
        score >= 60 && scoreInfo.color.replace('bg-', 'ring-')
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-base">Risk Assessment</h3>
        <div className={cn(
          "px-4 py-2 rounded-full text-sm font-bold",
          scoreInfo.bgColor,
          scoreInfo.textColor,
          score >= 60 && "animate-pulse"
        )}>
          {scoreInfo.level} Risk
        </div>
      </div>

      <div className="text-center mb-6">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="relative inline-flex items-center justify-center w-28 h-28 mb-4"
        >
          {/* Background circle */}
          <div className="absolute inset-0 rounded-full bg-background/40" />
          
          {/* Progress circle */}
          <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="40"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-background/60"
            />
            <motion.circle
              cx="50"
              cy="50"
              r="40"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              className={scoreInfo.textColor}
              initial={{ strokeDasharray: "0 251.2" }}
              animate={{ strokeDasharray: `${(percentage / 100) * 251.2} 251.2` }}
              transition={{ delay: 0.3, duration: 1, ease: "easeOut" }}
            />
          </svg>
          
          {/* Score text */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="relative z-10 text-center"
          >
            <div className="text-lg font-bold">{score}</div>
            <div className="text-xs text-muted-foreground">/ 100</div>
          </motion.div>
        </motion.div>
      </div>

      <div className="space-y-3">
        <div className="text-sm text-center text-muted-foreground">
          {getScoreDescription(score)}
        </div>

        <div className="relative h-2 bg-background/40 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className={cn("h-full rounded-full", scoreInfo.color)}
          />
        </div>

        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Safe</span>
          <span>Critical</span>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-border/20">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="font-medium">Triage</div>
            <div className="text-muted-foreground">Priority</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{scoreInfo.level}</div>
            <div className="text-muted-foreground">Risk Level</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{score}%</div>
            <div className="text-muted-foreground">Confidence</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}