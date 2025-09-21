import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import TextAnalyzer from './TextAnalyzer';
import ClassificationDisplay from './ClassificationDisplay';
import SignificanceDisplay from './SignificanceDisplay';
import SummaryDisplay from './SummaryDisplay';
import { module2Service } from '../../services/module2Service';

export default function Component2({ scrapedContent, onClearScrapedContent }) {
  const [text, setText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [serviceStatus, setServiceStatus] = useState('checking'); // 'checking', 'healthy', 'unhealthy'
  const [showScrapedContentTab, setShowScrapedContentTab] = useState(false);

  // Auto-populate with scraped content when available
  useEffect(() => {
    if (scrapedContent && scrapedContent.content) {
      // Don't populate text input - just show the tab
      setShowScrapedContentTab(true);
      // Clear any existing results when new content arrives
      setAnalysisResult(null);
      setError(null);
    }
  }, [scrapedContent]);

  // Check service health on component mount
  useEffect(() => {
    const checkServiceHealth = async () => {
      try {
        await module2Service.checkHealth();
        setServiceStatus('healthy');
      } catch (err) {
        console.error('Service health check failed:', err);
        setServiceStatus('unhealthy');
      }
    };

    checkServiceHealth();
  }, []);

  const analyzeText = async () => {
    // Combine attached content with user input
    let combinedText = '';
    
    if (scrapedContent && scrapedContent.content && showScrapedContentTab) {
      combinedText = scrapedContent.content;
      if (text.trim()) {
        combinedText += '\n\n--- Additional Context ---\n' + text.trim();
      }
    } else {
      combinedText = text.trim();
    }

    if (!combinedText) {
      setError('Please enter text to analyze or attach content from URL validation');
      return;
    }

    if (serviceStatus !== 'healthy') {
      setError('Misinformation Analysis service is not available');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const result = await module2Service.analyzeText(combinedText);
      setAnalysisResult(result);
      
    } catch (err) {
      setError(err.message || 'Failed to analyze text');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && e.ctrlKey && !isAnalyzing) {
      analyzeText();
    }
  };

  const clearResults = () => {
    setAnalysisResult(null);
    setError(null);
    setText('');
    // Keep the attached content tab unless explicitly dismissed
  };

  const dismissScrapedContent = () => {
    setShowScrapedContentTab(false);
    if (onClearScrapedContent) onClearScrapedContent();
  };

  return (
    <section className="w-full min-h-0 flex flex-col rounded-xl border border-border bg-card/20 backdrop-blur-sm shadow-sm">
      <div className="flex items-center justify-between p-6 pb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold tracking-tight">Misinformation Analyzer</h2>
          <div className={cn(
            "w-2 h-2 rounded-full transition-colors",
            serviceStatus === 'healthy' ? 'bg-green-500' :
            serviceStatus === 'unhealthy' ? 'bg-red-500' : 
            'bg-yellow-500 animate-pulse'
          )} title={
            serviceStatus === 'healthy' ? 'Service is healthy' :
            serviceStatus === 'unhealthy' ? 'Service is unavailable' :
            'Checking service status...'
          } />
        </div>
        <div className="flex gap-2">
          {(analysisResult || error) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearResults}
              className="text-xs"
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Scraped Content Tab - Small VS Code Copilot-style attachment */}
      <AnimatePresence>
        {showScrapedContentTab && scrapedContent && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="mx-6 mb-3"
          >
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/30 rounded-full px-3 py-1.5 text-sm">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-blue-600 dark:text-blue-400 font-medium">
                Attached: URL Content
              </span>
              <span className="text-blue-500/70 text-xs">
                ({scrapedContent.content.length} chars)
              </span>
              <button
                onClick={() => {
                  setShowScrapedContentTab(false);
                  if (onClearScrapedContent) onClearScrapedContent();
                }}
                className="ml-1 text-blue-500/70 hover:text-blue-600 transition-colors"
              >
                ✕
              </button>
            </div>
            
            {/* Expandable preview on hover/click */}
            <div className="mt-2 text-xs text-blue-600/70">
              <details className="cursor-pointer">
                <summary className="hover:text-blue-600 transition-colors">Preview content</summary>
                <div className="mt-2 p-3 bg-blue-500/5 border border-blue-500/20 rounded text-muted-foreground max-h-60 overflow-y-auto scrollbar-thin">
                  <div className="text-xs mb-2 text-blue-600/80 font-medium">Source: {scrapedContent.sourceUrl}</div>
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">
                    {scrapedContent.content}
                  </div>
                </div>
              </details>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Section - Always at Top */}
      <div className="px-6 pb-4">
        {serviceStatus === 'unhealthy' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/10 border border-red-500/20 rounded-md p-3 mb-4"
          >
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
              <span>!</span>
              Misinformation Analysis service is currently unavailable. Please check if the orchestrator is running.
            </div>
          </motion.div>
        )}

        <TextAnalyzer
          text={text}
          setText={setText}
          onAnalyze={analyzeText}
          onKeyPress={handleKeyPress}
          isAnalyzing={isAnalyzing}
          error={error}
          disabled={serviceStatus !== 'healthy'}
          hasAttachedContent={showScrapedContentTab && scrapedContent}
        />

        {/* Empty State - Only When No Results */}
        {!analysisResult && !error && (
          <div className="flex items-center justify-center min-h-[150px] mt-6">
            <div className="text-center text-muted-foreground">
              <div className="text-4xl mb-2">•</div>
              <p className="text-sm">Enter text above to analyze for misinformation</p>
              <p className="text-xs opacity-60 mt-1">
                Classification • Significance Scoring • Summarization
              </p>
              <p className="text-xs opacity-40 mt-1">
                Press Ctrl+Enter to analyze
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Results Section - Prominently Displayed When Available */}
      <AnimatePresence mode="wait">
        {analysisResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="px-6 pb-6 border-t border-border/50"
          >
            <div className="pt-6 space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <h3 className="text-base font-semibold text-green-600 dark:text-green-400">Analysis Results</h3>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <ClassificationDisplay 
                  classification={analysisResult.classification}
                  hasSource={analysisResult.source}
                />
                <SignificanceDisplay 
                  score={analysisResult.significance_score}
                />
              </div>
              
              <SummaryDisplay 
                summary={analysisResult.summary}
                originalText={text}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}