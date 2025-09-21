import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import URLValidator from './URLValidator';
import SafetyIndicator from './SafetyIndicator';
import ContentDisplay from './ContentDisplay';
import { module1Service } from '../../services/module1Service';

export default function Component1({ onScrapedContent }) {
  const [url, setUrl] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState(null);
  const [serviceStatus, setServiceStatus] = useState('checking'); // 'checking', 'healthy', 'unhealthy'
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [pendingScrapedContent, setPendingScrapedContent] = useState(null);

  // Check service health on component mount
  useEffect(() => {
    const checkServiceHealth = async () => {
      try {
        await module1Service.checkHealth();
        setServiceStatus('healthy');
      } catch (err) {
        console.error('Service health check failed:', err);
        setServiceStatus('unhealthy');
      }
    };

    checkServiceHealth();
  }, []);

  const validateURL = async () => {
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (serviceStatus !== 'healthy') {
      setError('URL Validator service is not available');
      return;
    }

    setIsValidating(true);
    setError(null);
    setValidationResult(null);

    try {
      const result = await module1Service.validateUrl(url.trim());
      setValidationResult(result);
      
      // Show permission dialog if scraped content is available
      if (result.content && onScrapedContent) {
        setPendingScrapedContent({
          content: result.content,
          sourceUrl: url.trim()
        });
        setShowPermissionDialog(true);
      }
      
    } catch (err) {
      setError(err.message || 'Failed to validate URL');
    } finally {
      setIsValidating(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isValidating) {
      validateURL();
    }
  };

  const clearResults = () => {
    setValidationResult(null);
    setError(null);
    setUrl('');
  };

  const handleSendToAnalyzer = () => {
    if (pendingScrapedContent && onScrapedContent) {
      onScrapedContent(pendingScrapedContent.content, pendingScrapedContent.sourceUrl);
    }
    setShowPermissionDialog(false);
    setPendingScrapedContent(null);
  };

  const handleDeclineTransfer = () => {
    setShowPermissionDialog(false);
    setPendingScrapedContent(null);
  };

  return (
    <section className="h-full flex flex-col rounded-xl border border-border bg-card/20 backdrop-blur-sm p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold tracking-tight">URL Validator</h2>
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
          {(validationResult || error) && (
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

      <div className="flex-1 flex flex-col space-y-4">
        {serviceStatus === 'unhealthy' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/10 border border-red-500/20 rounded-md p-3 mb-4"
          >
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
              <span>!</span>
              URL Validator service is currently unavailable. Please check if the orchestrator is running.
            </div>
          </motion.div>
        )}

        <URLValidator
          url={url}
          setUrl={setUrl}
          onValidate={validateURL}
          onKeyPress={handleKeyPress}
          isValidating={isValidating}
          error={error}
          disabled={serviceStatus !== 'healthy'}
        />

        <AnimatePresence mode="wait">
          {validationResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-4"
            >
              <SafetyIndicator 
                safe={validationResult.safe}
                url={url}
              />
              
              {validationResult.safe && validationResult.content && (
                <ContentDisplay content={validationResult.content} />
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {!validationResult && !error && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <div className="text-4xl mb-2">•</div>
              <p className="text-sm">Enter a URL to validate its safety</p>
              <p className="text-xs opacity-60 mt-1">
                Uses Google Safe Browsing & VirusTotal
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Inline Permission Prompt - Bottom of Component */}
      <AnimatePresence>
        {showPermissionDialog && pendingScrapedContent && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3 }}
            className="mx-6 mb-6 border-2 border-blue-500/30 rounded-lg bg-blue-500/5 backdrop-blur-sm overflow-hidden"
          >
            <div className="p-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1">
                  <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-2">
                    Content Ready for Misinformation Analysis
                  </h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    This URL contains text content that can be analyzed. Would you like to send it to the Misinformation Analyzer below?
                  </p>
                  
                  <div className="bg-background/50 rounded-md p-3 mb-4 border border-border/30">
                    <p className="text-xs text-muted-foreground mb-1">Source URL:</p>
                    <p className="text-sm font-mono text-blue-600 mb-2 break-all">{pendingScrapedContent.sourceUrl}</p>
                    
                    <p className="text-xs text-muted-foreground mb-1">Content Preview:</p>
                    <div className="text-sm max-h-16 overflow-y-auto text-muted-foreground scrollbar-thin">
                      {pendingScrapedContent.content.slice(0, 300)}
                      {pendingScrapedContent.content.length > 300 && '...'}
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <Button
                      onClick={handleSendToAnalyzer}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white"
                      size="sm"
                    >
                      ✓ Send to Analyzer
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={handleDeclineTransfer}
                      className="px-4 py-2 text-muted-foreground hover:text-foreground"
                      size="sm"
                    >
                      ✕ No Thanks
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
