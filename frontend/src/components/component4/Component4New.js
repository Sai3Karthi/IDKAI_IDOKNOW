import React, { useState, useRef, useEffect } from 'react';
import { motion } from "motion/react";
import { Button } from '../ui/button';
import { TextGenerateEffect } from '../ui/text-generate-effect';
import { Cover } from '../ui/cover';

// Orchestrator backend port (same as other modules)
const ORCHESTRATOR_PORT = process.env.REACT_APP_ORCHESTRATOR_PORT || 8000;
const ORCHESTRATOR_HTTP = `http://localhost:${ORCHESTRATOR_PORT}`;

export default function Component4() {
  const [stage, setStage] = useState('idle'); // idle|research-running|completed|error
  const [analysisMode, setAnalysisMode] = useState('fast'); // 'fast'|'slow'
  const [showModeSelection, setShowModeSelection] = useState(false);
  const [progress, setProgress] = useState({ leftist: 0, rightist: 0 });
  const [error, setError] = useState(null);
  const [leftistResults, setLeftistResults] = useState(null);
  const [rightistResults, setRightistResults] = useState(null);
  const [jobIds, setJobIds] = useState({ leftist: null, rightist: null });
  const pollRef = useRef(null);
  const [showJsonOutput, setShowJsonOutput] = useState(false);
  const [agentLogs, setAgentLogs] = useState({ leftist: [], rightist: [] });
  
  // New states for streaming content
  const [leftistContent, setLeftistContent] = useState('');
  const [rightistContent, setRightistContent] = useState('');
  const [leftistTyping, setLeftistTyping] = useState(false);
  const [rightistTyping, setRightistTyping] = useState(false);
  const [leftistStreamContent, setLeftistStreamContent] = useState('');
  const [rightistStreamContent, setRightistStreamContent] = useState('');
  const leftistTypingRef = useRef(null);
  const rightistTypingRef = useRef(null);
  const leftistProgressRef = useRef(0);
  const rightistProgressRef = useRef(0);

  // Smooth progress animation
  const animateProgress = (agent, targetProgress) => {
    const currentProgress = agent === 'leftist' ? leftistProgressRef.current : rightistProgressRef.current;
    const progressDiff = targetProgress - currentProgress;
    const steps = 30; // 30 steps for smooth animation
    const stepSize = progressDiff / steps;
    let currentStep = 0;

    const progressInterval = setInterval(() => {
      currentStep++;
      const newProgress = currentProgress + (stepSize * currentStep);
      
      if (agent === 'leftist') {
        leftistProgressRef.current = Math.min(newProgress, targetProgress);
        setProgress(prev => ({ ...prev, leftist: leftistProgressRef.current }));
      } else {
        rightistProgressRef.current = Math.min(newProgress, targetProgress);
        setProgress(prev => ({ ...prev, rightist: rightistProgressRef.current }));
      }

      if (currentStep >= steps || newProgress >= targetProgress) {
        clearInterval(progressInterval);
        if (agent === 'leftist') {
          leftistProgressRef.current = targetProgress;
          setProgress(prev => ({ ...prev, leftist: targetProgress }));
        } else {
          rightistProgressRef.current = targetProgress;
          setProgress(prev => ({ ...prev, rightist: targetProgress }));
        }
      }
    }, 50); // Update every 50ms for smooth animation
  };

  // Typewriter effect for streaming content
  const typeWriterEffect = (text, agent, speed = 30) => {
    if (agent === 'leftist') {
      setLeftistTyping(true);
      setLeftistStreamContent('');
    } else {
      setRightistTyping(true);
      setRightistStreamContent('');
    }

    let index = 0;
    const typeInterval = setInterval(() => {
      if (index < text.length) {
        if (agent === 'leftist') {
          setLeftistStreamContent(prev => prev + text[index]);
        } else {
          setRightistStreamContent(prev => prev + text[index]);
        }
        index++;
      } else {
        clearInterval(typeInterval);
        if (agent === 'leftist') {
          setLeftistTyping(false);
        } else {
          setRightistTyping(false);
        }
      }
    }, speed);

    if (agent === 'leftist') {
      leftistTypingRef.current = typeInterval;
    } else {
      rightistTypingRef.current = typeInterval;
    }
  };

  // Add log message to the agent logs
  const addLog = (message, type = 'info', agent = 'both') => {
    const timestamp = new Date().toLocaleTimeString();
    setAgentLogs(prev => {
      if (agent === 'both') {
        return {
          leftist: [...prev.leftist, { message, type, timestamp }],
          rightist: [...prev.rightist, { message, type, timestamp }]
        };
      } else {
        return {
          ...prev,
          [agent]: [...prev[agent], { message, type, timestamp }]
        };
      }
    });
  };

  // Start deep research analysis
  const startDeepResearch = async () => {
    if (stage !== 'idle' && stage !== 'completed' && stage !== 'error') return;
    
    setStage('research-running');
    setError(null);
    setProgress({ leftist: 0, rightist: 0 });
    leftistProgressRef.current = 0;
    rightistProgressRef.current = 0;
    setLeftistResults(null);
    setRightistResults(null);
    setAgentLogs({ leftist: [], rightist: [] });
    setLeftistStreamContent('');
    setRightistStreamContent('');
    setLeftistTyping(false);
    setRightistTyping(false);
    setShowModeSelection(false);

    try {
      addLog('Starting deep research agents...', 'info');
      
      // Start both agents simultaneously
      const [leftistResponse, rightistResponse] = await Promise.all([
        fetch(`${ORCHESTRATOR_HTTP}/module4/leftist/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: analysisMode })
        }),
        fetch(`${ORCHESTRATOR_HTTP}/module4/rightist/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: analysisMode })
        })
      ]);

      const leftistData = await leftistResponse.json();
      const rightistData = await rightistResponse.json();

      setJobIds({ leftist: leftistData.job_id, rightist: rightistData.job_id });
      
      addLog(`Leftist agent started (Job: ${leftistData.job_id})`, 'success', 'leftist');
      addLog(`Rightist agent started (Job: ${rightistData.job_id})`, 'success', 'rightist');
      
      // Start polling
      pollProgress(leftistData.job_id, rightistData.job_id);
      
    } catch (e) {
      addLog(`Failed to start research: ${e.message}`, 'error');
      setError(e.message);
      setStage('error');
    }
  };

  // Show mode selection dialog
  const showAnalysisModeDialog = () => {
    setShowModeSelection(true);
  };

  // Poll for progress updates
  const pollProgress = (leftistJobId, rightistJobId) => {
    pollRef.current = setInterval(async () => {
      try {
        const [leftistResponse, rightistResponse] = await Promise.all([
          fetch(`${ORCHESTRATOR_HTTP}/module4/leftist/status/${leftistJobId}`),
          fetch(`${ORCHESTRATOR_HTTP}/module4/rightist/status/${rightistJobId}`)
        ]);
        
        const leftistData = await leftistResponse.json();
        const rightistData = await rightistResponse.json();
        
        // Animate progress smoothly
        animateProgress('leftist', leftistData.progress || 0);
        animateProgress('rightist', rightistData.progress || 0);
        
        // Update logs
        if (leftistData.message) {
          addLog(leftistData.message, leftistData.status === 'error' ? 'error' : 'info', 'leftist');
        }
        if (rightistData.message) {
          addLog(rightistData.message, rightistData.status === 'error' ? 'error' : 'info', 'rightist');
        }

        // Check completion
        if (leftistData.status === 'completed' && rightistData.status === 'completed') {
          addLog('Both agents completed successfully!', 'success');
          setStage('completed');
          clearInterval(pollRef.current);
          
          // Fetch results and start typewriter effect
          fetchAgentResults('leftist', leftistJobId);
          fetchAgentResults('rightist', rightistJobId);
        }
        
        // Check for errors
        if (leftistData.status === 'error' || rightistData.status === 'error') {
          const errorMsg = leftistData.error || rightistData.error || 'Unknown error';
          addLog(`Research error: ${errorMsg}`, 'error');
          setError(errorMsg);
          setStage('error');
          clearInterval(pollRef.current);
        }
      } catch (e) {
        addLog(`Polling error: ${e.message}`, 'error');
      }
    }, 2000); // Poll every 2 seconds for more responsive updates
  };

  // Fetch agent results and trigger typewriter effect
  const fetchAgentResults = async (agentType, jobId) => {
    try {
      const response = await fetch(`${ORCHESTRATOR_HTTP}/module4/${agentType}/results/${jobId}`);
      if (!response.ok) return;
      
      const data = await response.json();
      
      if (agentType === 'leftist') {
        setLeftistResults(data);
        // Start typewriter effect for leftist content
        const content = generateDisplayContent(data);
        typeWriterEffect(content, 'leftist');
      } else if (agentType === 'rightist') {
        setRightistResults(data);
        // Start typewriter effect for rightist content
        const content = generateDisplayContent(data);
        typeWriterEffect(content, 'rightist');
      }
      
    } catch (e) {
      addLog(`Error fetching ${agentType} results: ${e.message}`, 'error', agentType);
    }
  };

  // Generate display content from results
  const generateDisplayContent = (results) => {
    if (!results) return 'Processing research data...';
    
    let content = `Research Analysis Complete\n\n`;
    content += `📊 Claims Processed: ${results.claims_processed || 0}\n`;
    content += `🔍 Total Sources: ${results.total_sources || 0}\n`;
    content += `⏱️ Processing Time: ${results.total_time ? (results.total_time / 60).toFixed(1) + ' minutes' : 'N/A'}\n`;
    content += `📈 Success Rate: ${results.success_rate_percent ? results.success_rate_percent.toFixed(1) + '%' : 'N/A'}\n\n`;
    
    if (results.claims_with_content && results.claims_with_content.length > 0) {
      content += `Research Findings:\n\n`;
      results.claims_with_content.slice(0, 3).forEach((claim, index) => {
        content += `${index + 1}. ${claim.claim_text}\n`;
        content += `   Sources: ${claim.sources_found ? claim.sources_found.length : 0}\n`;
        content += `   Content Extracted: ${claim.extracted_content ? claim.extracted_content.length : 0} pieces\n\n`;
      });
    }
    
    return content;
  };

  // Get log styling based on type
  const getLogStyle = (type) => {
    switch(type) {
      case 'error': return 'text-red-400';
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      default: return 'text-gray-300';
    }
  };

  // Reset to idle state
  const resetComponent = () => {
    setStage('idle');
    setProgress({ leftist: 0, rightist: 0 });
    leftistProgressRef.current = 0;
    rightistProgressRef.current = 0;
    setError(null);
    setLeftistResults(null);
    setRightistResults(null);
    setJobIds({ leftist: null, rightist: null });
    setAgentLogs({ leftist: [], rightist: [] });
    setLeftistStreamContent('');
    setRightistStreamContent('');
    setLeftistTyping(false);
    setRightistTyping(false);
    setShowJsonOutput(false);
    setShowModeSelection(false);
    clearInterval(pollRef.current);
    clearInterval(leftistTypingRef.current);
    clearInterval(rightistTypingRef.current);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(pollRef.current);
      clearInterval(leftistTypingRef.current);
      clearInterval(rightistTypingRef.current);
    };
  }, []);

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6 bg-white text-black min-h-[600px]">
      {/* Header */}
      <div className="text-center space-y-2 border-b border-gray-200 pb-4">
        <h2 className="text-2xl font-bold text-black">Module 4: Deep Research Engine</h2>
        <p className="text-gray-600 text-sm">Parallel analysis of political perspectives with comprehensive research</p>
      </div>

      {/* Analysis Mode Selection Modal */}
      {showModeSelection && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white border border-gray-300 rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-black mb-4">Select Analysis Mode</h3>
            
            <div className="space-y-4">
              <div 
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  analysisMode === 'fast' ? 'border-black bg-gray-100' : 'border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => setAnalysisMode('fast')}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    analysisMode === 'fast' ? 'border-black bg-black' : 'border-gray-400'
                  }`}>
                    {analysisMode === 'fast' && <div className="w-2 h-2 bg-white rounded-full m-0.5" />}
                  </div>
                  <div>
                    <div className="font-medium text-black">⚡ Fast Analysis</div>
                    <div className="text-xs text-gray-600">~3-5 minutes • Limited sources</div>
                  </div>
                </div>
              </div>
              
              <div 
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  analysisMode === 'slow' ? 'border-black bg-gray-100' : 'border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => setAnalysisMode('slow')}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    analysisMode === 'slow' ? 'border-black bg-black' : 'border-gray-400'
                  }`}>
                    {analysisMode === 'slow' && <div className="w-2 h-2 bg-white rounded-full m-0.5" />}
                  </div>
                  <div>
                    <div className="font-medium text-black">🔍 Comprehensive Analysis</div>
                    <div className="text-xs text-gray-600">~8-12 minutes • Complete research</div>
                  </div>
                </div>
              </div>
            </div>
            
            {analysisMode === 'fast' && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg mt-4">
                <div className="flex items-start gap-2">
                  <div className="text-yellow-600 mt-0.5">⚠️</div>
                  <div className="text-xs">
                    <div className="font-medium text-yellow-700">Accuracy Warning</div>
                    <div className="text-gray-600">
                      Fast analysis uses fewer sources and may have reduced accuracy compared to comprehensive analysis.
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex gap-2 pt-4">
              <Button 
                variant="outline" 
                onClick={() => setShowModeSelection(false)} 
                className="flex-1 border-gray-300 text-black hover:bg-gray-50"
              >
                Cancel
              </Button>
              <Button 
                onClick={startDeepResearch} 
                className="flex-1 bg-black text-white hover:bg-gray-800"
              >
                Start Research
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {stage === 'error' && (
        <div className="p-5 text-center space-y-4 text-red-600 border border-red-300 rounded-lg bg-red-50">
          <p className="text-sm">Error: {error}</p>
          <Button 
            variant="outline" 
            onClick={resetComponent}
            className="border-red-300 text-red-600 hover:bg-red-50"
          >
            Reset Module 4
          </Button>
        </div>
      )}
      
      {/* Idle State - Deep Research Button */}
      {stage === 'idle' && (
        <div className="space-y-6">
          <div className="text-center space-y-4">
            <h3 className="text-lg font-medium text-black">
              Ready for Deep Research
            </h3>
            <p className="text-sm text-gray-600">
              Analyze Module 3 perspectives with comprehensive research agents
            </p>
          </div>
          
          <div className="flex justify-center">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button 
                onClick={showAnalysisModeDialog}
                size="lg"
                className="px-8 py-3 text-base font-semibold bg-black text-white hover:bg-gray-800"
              >
                🔬 Deep Analysis Research
              </Button>
            </motion.div>
          </div>
          
          <div className="text-center text-xs text-gray-500 space-y-1">
            <div>📊 Leftist Agent: Analyzes leftist + common perspectives</div>
            <div>📊 Rightist Agent: Analyzes rightist + common perspectives</div>
            <div>⚡ Both agents run in parallel for efficient processing</div>
          </div>
        </div>
      )}
      
      {/* Processing State - Parallel Research */}
      {stage === 'research-running' && (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-black">
              Deep Research in Progress ({analysisMode.toUpperCase()} mode)
            </h3>
          </div>
          
          {/* Parallel Progress Bars */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Leftist Agent Progress */}
            <div className="p-4 border border-gray-300 rounded-lg bg-white">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-2 w-2 rounded-full bg-black animate-pulse" />
                  <span className="text-sm font-medium text-black">🔴 Leftist Research Agent</span>
                </div>
                <p className="text-xs text-gray-600">Progress: {progress.leftist.toFixed(1)}%</p>
                <div className="w-full h-3 bg-gray-200 rounded-md overflow-hidden">
                  <div
                    className="h-full bg-black transition-all duration-500 ease-out"
                    style={{ width: `${progress.leftist}%` }}
                  />
                </div>
              </div>
            </div>
            
            {/* Rightist Agent Progress */}
            <div className="p-4 border border-gray-300 rounded-lg bg-white">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-2 w-2 rounded-full bg-black animate-pulse" />
                  <span className="text-sm font-medium text-black">🔵 Rightist Research Agent</span>
                </div>
                <p className="text-xs text-gray-600">Progress: {progress.rightist.toFixed(1)}%</p>
                <div className="w-full h-3 bg-gray-200 rounded-md overflow-hidden">
                  <div
                    className="h-full bg-black transition-all duration-500 ease-out"
                    style={{ width: `${progress.rightist}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
          
          {/* Agent Logs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Leftist Agent Logs */}
            <div className="p-4 bg-black rounded-lg border border-gray-300">
              <h4 className="text-sm font-medium mb-3 text-white">🔴 Leftist Agent Logs</h4>
              <div className="space-y-1 max-h-32 overflow-y-auto font-mono text-xs">
                {agentLogs.leftist.slice(-10).map((log, index) => (
                  <div key={index} className="flex gap-2">
                    <span className="text-gray-400">[{log.timestamp}]</span>
                    <span className={getLogStyle(log.type)}>{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Rightist Agent Logs */}
            <div className="p-4 bg-black rounded-lg border border-gray-300">
              <h4 className="text-sm font-medium mb-3 text-white">🔵 Rightist Agent Logs</h4>
              <div className="space-y-1 max-h-32 overflow-y-auto font-mono text-xs">
                {agentLogs.rightist.slice(-10).map((log, index) => (
                  <div key={index} className="flex gap-2">
                    <span className="text-gray-400">[{log.timestamp}]</span>
                    <span className={getLogStyle(log.type)}>{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Completed State - ChatGPT-like Dual Results Display */}
      {stage === 'completed' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-black">Deep Research Complete</h3>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowJsonOutput(!showJsonOutput)}
                className="border-gray-300 text-black hover:bg-gray-50"
              >
                {showJsonOutput ? 'Hide' : 'Show'} Raw Data
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={resetComponent}
                className="border-gray-300 text-black hover:bg-gray-50"
              >
                New Research
              </Button>
            </div>
          </div>
          
          {/* ChatGPT-style Dual Results Boxes */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Leftist Results Box - ChatGPT Style */}
            <div className="space-y-4">
              <div className="border border-gray-300 rounded-lg bg-white">
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <h3 className="font-semibold text-base flex items-center gap-2 text-black">
                    🔴 Leftist Research Analysis
                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                      Leftist + Common
                    </span>
                  </h3>
                </div>
                
                <div className="p-4">
                  {leftistStreamContent ? (
                    <div className="space-y-2">
                      <pre className="text-sm text-black whitespace-pre-wrap font-mono leading-relaxed">
                        {leftistStreamContent}
                        {leftistTyping && (
                          <span className="inline-block w-2 h-4 bg-black animate-pulse ml-1" />
                        )}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <div className="animate-pulse">Processing leftist research...</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* Rightist Results Box - ChatGPT Style */}
            <div className="space-y-4">
              <div className="border border-gray-300 rounded-lg bg-white">
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <h3 className="font-semibold text-base flex items-center gap-2 text-black">
                    🔵 Rightist Research Analysis
                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                      Rightist + Common
                    </span>
                  </h3>
                </div>
                
                <div className="p-4">
                  {rightistStreamContent ? (
                    <div className="space-y-2">
                      <pre className="text-sm text-black whitespace-pre-wrap font-mono leading-relaxed">
                        {rightistStreamContent}
                        {rightistTyping && (
                          <span className="inline-block w-2 h-4 bg-black animate-pulse ml-1" />
                        )}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <div className="animate-pulse">Processing rightist research...</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          
          {/* Raw Data Display */}
          {showJsonOutput && (
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-black">Raw Research Data</h4>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="p-4 bg-black rounded border border-gray-300">
                  <h5 className="text-xs font-medium mb-2 text-white">Leftist Agent Data</h5>
                  <pre className="text-xs text-green-400 overflow-auto max-h-64 font-mono">
                    {JSON.stringify(leftistResults, null, 2)}
                  </pre>
                </div>
                <div className="p-4 bg-black rounded border border-gray-300">
                  <h5 className="text-xs font-medium mb-2 text-white">Rightist Agent Data</h5>
                  <pre className="text-xs text-green-400 overflow-auto max-h-64 font-mono">
                    {JSON.stringify(rightistResults, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}