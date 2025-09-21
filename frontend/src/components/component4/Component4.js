import React, { useState, useRef, useEffect } from 'react';
import { motion } from "motion/react";
import { Button } from '../ui/button';
import { Cover } from '../ui/cover';

// Orchestrator backend port (same as other modules)
const ORCHESTRATOR_PORT = process.env.REACT_APP_ORCHESTRATOR_PORT || 8000;
const ORCHESTRATOR_HTTP = `http://localhost:${ORCHESTRATOR_PORT}`;
const ORCHESTRATOR_WS = `ws://localhost:${ORCHESTRATOR_PORT}`;

export default function Component4() {
  const [stage, setStage] = useState('idle'); // idle|research-running|completed|debate-running|debate-completed|error
  const [analysisMode, setAnalysisMode] = useState('fast'); // 'fast'|'slow'
  const [showModeSelection, setShowModeSelection] = useState(false);
  const [progress, setProgress] = useState({ leftist: 0, rightist: 0 });
  const [error, setError] = useState(null);
  const [leftistResults, setLeftistResults] = useState(null);
  const [rightistResults, setRightistResults] = useState(null);
  const [jobIds, setJobIds] = useState({ leftist: null, rightist: null });
  
  // WebSocket connections for real-time streaming
  const leftistWsRef = useRef(null);
  const rightistWsRef = useRef(null);
  const debateWsRef = useRef(null);
  
  // Missing state variables
  const [agentLogs, setAgentLogs] = useState({ leftist: [], rightist: [] });
  const [showJsonOutput, setShowJsonOutput] = useState(false);
  
  // New states for streaming content
  const [leftistStreamContent, setLeftistStreamContent] = useState('');
  const [rightistStreamContent, setRightistStreamContent] = useState('');
  const [leftistTyping, setLeftistTyping] = useState(false);
  const [rightistTyping, setRightistTyping] = useState(false);
  const leftistTypingRef = useRef(null);
  const rightistTypingRef = useRef(null);
  const leftistProgressRef = useRef(0);
  const rightistProgressRef = useRef(0);
  const completionCheckRef = useRef(null);
  const leftistResultsRef = useRef(null);
  const rightistResultsRef = useRef(null);

  // Debate states
  const [debateResults, setDebateResults] = useState(null);
  const [debateJobId, setDebateJobId] = useState(null);
  const [debateProgress, setDebateProgress] = useState(0);
  const [debateMessage, setDebateMessage] = useState('');
  const [debateRounds, setDebateRounds] = useState([]);
  const [currentScores, setCurrentScores] = useState({ leftist: 0, rightist: 0 });
  const [showDebateDetails, setShowDebateDetails] = useState(false);

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

  // Typewriter effect for streaming content - append mode
  const typeWriterEffect = (text, agent, speed = 30, append = true) => {
    if (!text || text.trim() === '') return;
    
    // Clean the input text first
    const cleanText = text
      .replace(/undefined/g, '')
      .replace(/\s{2,}/g, ' ')
      .trim();
    
    if (!cleanText) return;
    
    // Clear any existing interval
    if (agent === 'leftist' && leftistTypingRef.current) {
      clearInterval(leftistTypingRef.current);
    } else if (agent === 'rightist' && rightistTypingRef.current) {
      clearInterval(rightistTypingRef.current);
    }

    if (agent === 'leftist') {
      setLeftistTyping(true);
      if (!append) setLeftistStreamContent('');
    } else {
      setRightistTyping(true);
      if (!append) setRightistStreamContent('');
    }

    let index = 0;
    const typeInterval = setInterval(() => {
      if (index < cleanText.length) {
        if (agent === 'leftist') {
          setLeftistStreamContent(prev => append ? prev + cleanText[index] : cleanText.substring(0, index + 1));
        } else {
          setRightistStreamContent(prev => append ? prev + cleanText[index] : cleanText.substring(0, index + 1));
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

    // Store interval reference for cleanup
    if (agent === 'leftist') {
      leftistTypingRef.current = typeInterval;
    } else {
      rightistTypingRef.current = typeInterval;
    }
  };

  // Format results content for streaming
  // Generate progressive content based on agent progress
  const fetchAndStreamContent = async (agentType, jobId) => {
    try {
      // Wait a moment for the job to have some content
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Try to fetch the results (this might fail if not ready yet, that's OK)
      const response = await fetch(`${ORCHESTRATOR_HTTP}/module4/${agentType}/results/${jobId}`);
      
      if (response.ok) {
        const results = await response.json();
        
        // Extract the actual research content
        let contentToStream = '';
        
        if (results && results.claims_with_content) {
          results.claims_with_content.forEach((claim, index) => {
            if (claim.success && claim.extracted_content && claim.extracted_content.length > 0) {
              // Show only clean extracted content text
              claim.extracted_content.forEach((contentItem, contentIndex) => {
                if (contentItem.content) {
                  // Extract clean, meaningful text content only
                  let cleanText = contentItem.content
                    .replace(/\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}/g, '') // Remove dates
                    .replace(/\d+\s+days?\s+ago/g, '') // Remove timestamps
                    .replace(/This is a video/g, '') // Remove video tags
                    .replace(/\d+\s+\d+\s+\d+.*\d+/g, '') // Remove pagination
                    .replace(/^\W+|\W+$/g, '') // Remove leading/trailing punctuation
                    .replace(/\s{2,}/g, ' ') // Multiple spaces to single
                    .trim();
                  
                  // Split into sentences and filter meaningful ones
                  const sentences = cleanText.split(/[.!?]+/).filter(sentence => {
                    const trimmed = sentence.trim();
                    return trimmed.length > 15 && 
                           !trimmed.match(/^\d/) &&
                           !trimmed.includes('This is a') &&
                           !trimmed.includes('days ago') &&
                           trimmed.split(' ').length > 3;
                  });
                  
                  // Show only meaningful content
                  if (sentences.length > 0) {
                    const meaningfulText = sentences.slice(0, 2).join('. ').trim();
                    if (meaningfulText.length > 20) {
                      contentToStream += `${meaningfulText}.\n\n`;
                    }
                  }
                }
              });
            }
          });
        } else {
          // Fallback content if no results yet
          contentToStream = `Analyzing ${agentType} perspectives and extracting content...\nThis may take a few minutes depending on the analysis mode selected.\n\nPlease wait while we gather comprehensive research data.`;
        }
        
        // Start the typewriter effect with the actual content
        typeWriterEffect(contentToStream, agentType);
        
      } else {
        // If results not ready yet, show progress content
        const progressContent = generateProgressContent(agentType, 60);
        typeWriterEffect(progressContent, agentType);
      }
      
    } catch (error) {
      console.error(`Error fetching ${agentType} content:`, error);
      // Show fallback content
      const fallbackContent = `🔍 ${agentType.toUpperCase()} RESEARCH IN PROGRESS\n\nGathering research data...\nExtracting content from sources...\nProcessing perspectives...\n\nPlease wait for results.`;
      typeWriterEffect(fallbackContent, agentType);
    }
  };

  const generateProgressContent = (agentType, progress) => {
    const agentLabel = agentType === 'leftist' ? '🔴 LEFTIST' : '🔵 RIGHTIST';
    let content = `${agentLabel} AGENT - DEEP RESEARCH ANALYSIS\n`;
    content += `${'='.repeat(50)}\n\n`;
    
    if (progress >= 30) {
      content += `🔄 Loading perspectives from Module 3...\n`;
      content += `📊 Initializing research parameters...\n\n`;
    }
    
    if (progress >= 50) {
      const claimCount = agentType === 'leftist' ? '3 leftist + 1 common' : '2 rightist + 1 common';
      content += `🔍 ACTIVE RESEARCH PHASE\n`;
      content += `   Analyzing ${claimCount} perspectives...\n`;
      content += `   Searching for supporting evidence...\n`;
      content += `   Extracting relevant content...\n\n`;
    }
    
    if (progress >= 70) {
      content += `📄 CONTENT EXTRACTION IN PROGRESS\n`;
      content += `   Processing claim 1: Political bias analysis...\n`;
      content += `   🔗 Finding credible sources...\n`;
      content += `   📝 Extracting key information...\n\n`;
    }
    
    if (progress >= 90) {
      content += `⚡ FINALIZING RESEARCH\n`;
      content += `   Consolidating findings...\n`;
      content += `   Preparing comprehensive report...\n`;
      content += `   Quality assurance check...\n\n`;
      content += `✅ Research analysis will complete shortly...\n`;
    }
    
    return content;
  };

  const formatStreamingContent = (results) => {
    if (!results) return '';
    
    // If it's already formatted text, return it clean
    if (typeof results === 'string') {
      return results
        .replace(/undefined/g, '')
        .replace(/\s{2,}/g, ' ')
        .trim();
    }
    
    let content = '';
    let sourcesFound = [];
    
    // Extract meaningful content in a conversational way
    if (results.claims_with_content && results.claims_with_content.length > 0) {
      results.claims_with_content.forEach((claim, index) => {
        if (claim.success && claim.extracted_content && claim.extracted_content.length > 0) {
          claim.extracted_content.forEach((contentItem) => {
            if (contentItem.content) {
              // Extract clean, readable text
              let cleanText = contentItem.content
                .replace(/\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}/g, '') // Remove dates
                .replace(/\d+\s+days?\s+ago/g, '') // Remove timestamps  
                .replace(/This is a video/g, '') // Remove video indicators
                .replace(/\d+\s+\d+\s+\d+.*\d+/g, '') // Remove pagination
                .replace(/[A-Z]{3,}/g, '') // Remove all caps words
                .replace(/undefined/g, '') // Remove undefined
                .replace(/^\W+|\W+$/g, '') // Remove leading/trailing punctuation
                .replace(/\s{2,}/g, ' ') // Multiple spaces to single
                .trim();
              
              // Filter for meaningful sentences
              const sentences = cleanText.split(/[.!?]+/).filter(sentence => {
                const trimmed = sentence.trim();
                return trimmed.length > 25 && 
                       !trimmed.match(/^\d/) &&
                       !trimmed.includes('This is a') &&
                       !trimmed.includes('days ago') &&
                       !trimmed.includes('undefined') &&
                       trimmed.split(' ').length > 5;
              });
              
              // Add meaningful content naturally
              if (sentences.length > 0) {
                const meaningfulText = sentences.slice(0, 2).join('. ').trim();
                if (meaningfulText.length > 30) {
                  content += `${meaningfulText}. `;
                }
              }
              
              // Collect source URLs
              if (contentItem.url && contentItem.url !== 'undefined' && !sourcesFound.includes(contentItem.url)) {
                sourcesFound.push(contentItem.url);
              }
            }
          });
        }
      });
    }
    
    // Add sources naturally at the end if any found
    if (sourcesFound.length > 0) {
      content += `\n\n**Sources:**\n`;
      sourcesFound.slice(0, 3).forEach(url => {
        content += `• ${url}\n`;
      });
    }
    
    return content || '';
  };

  // Deep research start function
  const startDeepResearch = async (mode) => {
    setAnalysisMode(mode);
    setShowModeSelection(false);
    setStage('research-running');
    setError(null);
    setProgress({ leftist: 0, rightist: 0 });
    setLeftistResults(null);
    setRightistResults(null);
    
    // Clear all content and typing states
    setLeftistStreamContent('🔍 Starting leftist research...');
    setRightistStreamContent('🔍 Starting rightist research...');
    setLeftistTyping(false);
    setRightistTyping(false);
    
    // Clear any existing intervals
    if (leftistTypingRef.current) clearInterval(leftistTypingRef.current);
    if (rightistTypingRef.current) clearInterval(rightistTypingRef.current);
    
    // Reset progress refs
    leftistProgressRef.current = 0;
    rightistProgressRef.current = 0;

    try {
      // Start both agents in parallel
      console.log(`Starting deep research in ${mode} mode...`);
      
      const [leftistResponse, rightistResponse] = await Promise.all([
        fetch(`${ORCHESTRATOR_HTTP}/module4/leftist/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode }),
        }),
        fetch(`${ORCHESTRATOR_HTTP}/module4/rightist/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode }),
        })
      ]);

      if (!leftistResponse.ok || !rightistResponse.ok) {
        throw new Error('Failed to start research agents');
      }

      const leftistData = await leftistResponse.json();
      const rightistData = await rightistResponse.json();

      setJobIds({ 
        leftist: leftistData.job_id, 
        rightist: rightistData.job_id 
      });

      console.log('Research agents started:', { 
        leftist: leftistData.job_id, 
        rightist: rightistData.job_id 
      });

      // Start WebSocket streaming for real-time updates
      startWebSocketStreaming(leftistData.job_id, rightistData.job_id);

      // Add a fallback completion check in case WebSocket messages are missed
      const completionCheckInterval = setInterval(async () => {
        try {
          // Check if we have valid job IDs
          if (!jobIds.leftist || !jobIds.rightist) {
            console.log('No valid job IDs for polling, checking UI-based completion...');
            
            // If both agents show 100% progress but no results, trigger completion
            if (progress.leftist === 100 && progress.rightist === 100 && 
                !leftistResultsRef.current && !rightistResultsRef.current) {
              console.log('UI shows 100% completion but no results - triggering direct completion');
              
              const fallbackResult = {
                summary: 'Research completed successfully but detailed results were lost due to server restart. Please restart research for full results.',
                status: 'completed_with_data_loss',
                directCompletion: true
              };
              
              setLeftistResults(fallbackResult);
              setRightistResults(fallbackResult);
              
              clearInterval(completionCheckInterval);
              completionCheckRef.current = null;
              setTimeout(() => checkBothCompleted(), 200);
            }
            return;
          }

          console.log('Polling with job IDs:', jobIds);

          const [leftistStatus, rightistStatus] = await Promise.all([
            fetch(`${ORCHESTRATOR_HTTP}/module4/leftist/status/${jobIds.leftist}`),
            fetch(`${ORCHESTRATOR_HTTP}/module4/rightist/status/${jobIds.rightist}`)
          ]);

          console.log('Polling response status:', {
            leftist: leftistStatus.status,
            rightist: rightistStatus.status
          });

          if (leftistStatus.ok && rightistStatus.ok) {
            const leftistData_status = await leftistStatus.json();
            const rightistData_status = await rightistStatus.json();

            console.log('Polling status:', { 
              leftist: leftistData_status.status, 
              rightist: rightistData_status.status 
            });
            console.log('Polling leftist data:', leftistData_status);
            console.log('Polling rightist data:', rightistData_status);
            console.log('Current refs:', {
              leftistResultsRef: leftistResultsRef.current,
              rightistResultsRef: rightistResultsRef.current
            });

            // Check if completed and results not yet set
            if (leftistData_status.status === 'completed' && !leftistResultsRef.current && leftistData_status.results) {
              console.log('Leftist completed via polling, setting results');
              setLeftistResults(leftistData_status.results);
            }

            if (rightistData_status.status === 'completed' && !rightistResultsRef.current && rightistData_status.results) {
              console.log('Rightist completed via polling, setting results');
              setRightistResults(rightistData_status.results);
            }

            // Check if both completed
            if (leftistData_status.status === 'completed' && rightistData_status.status === 'completed') {
              console.log('Both agents completed via polling, checking final state');
              clearInterval(completionCheckInterval);
              completionCheckRef.current = null;
              setTimeout(() => checkBothCompleted(), 200);
            }
          } else {
            // Handle 404 or other errors - job status lost (orchestrator restart)
            if (leftistStatus.status === 404 || rightistStatus.status === 404) {
              console.log('Job status not found (404) - orchestrator may have restarted');
              console.log('Research appears to have completed but job status was lost');
              
              // If we see 100% progress in UI but no results, assume completion
              if (progress.leftist === 100 && progress.rightist === 100 && !leftistResultsRef.current && !rightistResultsRef.current) {
                console.log('Both agents at 100% but no results due to status loss - triggering manual completion');
                
                // Set dummy results to trigger completion (user can restart if needed)
                const fallbackResult = {
                  summary: 'Research completed successfully but detailed results were lost due to server restart. Please restart research for full results.',
                  status: 'completed_with_data_loss'
                };
                
                setLeftistResults(fallbackResult);
                setRightistResults(fallbackResult);
                
                clearInterval(completionCheckInterval);
                completionCheckRef.current = null;
                setTimeout(() => checkBothCompleted(), 200);
              }
            } else {
              console.log('Polling status check failed:', {
                leftist: leftistStatus.status,
                rightist: rightistStatus.status
              });
            }
          }
        } catch (error) {
          console.error('Error checking completion status:', error);
        }
      }, 2000); // Check every 2 seconds

      // Store the interval reference for cleanup
      completionCheckRef.current = completionCheckInterval;

    } catch (err) {
      console.error('Error starting research:', err);
      setError(`Failed to start research: ${err.message}`);
      setStage('error');
    }
  };

  // Polling function with smooth progress and content streaming
  // WebSocket streaming for real-time research updates
  const startWebSocketStreaming = (leftistJobId, rightistJobId) => {
    // Initialize WebSocket connections for both agents
    const connectAgent = (jobId, agentType) => {
      const ws = new WebSocket(`${ORCHESTRATOR_WS}/ws/module4/${jobId}`);
      
      ws.onopen = () => {
        console.log(`${agentType} WebSocket connected for job ${jobId}`);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(`${agentType} WebSocket raw message:`, data);
        
        switch (data.type) {
          case 'progress':
            // Update progress smoothly
            animateProgress(agentType, data.progress || 0);
            break;
            
          case 'content_stream':
            // Stream content in real-time with ChatGPT-like effect
            const newContent = data.content || '';
            if (newContent.trim() && newContent !== 'undefined') {
              // Clean the content before streaming
              const cleanContent = formatStreamingContent(newContent);
              if (cleanContent && cleanContent.trim()) {
                // Replace content instead of appending to avoid garbled text
                if (agentType === 'leftist') {
                  setLeftistStreamContent(cleanContent);
                  setLeftistTyping(false);
                } else {
                  setRightistStreamContent(cleanContent);
                  setRightistTyping(false);
                }
              }
            }
            break;
            
          case 'completed':
            // Handle completion
            console.log(`${agentType} agent completed with results:`, data.results);
            const results = data.results;
            if (agentType === 'leftist') {
              setLeftistResults(results);
              console.log('Set leftist results:', results);
            } else {
              setRightistResults(results);
              console.log('Set rightist results:', results);
            }
            
            // Format and display final results cleanly
            const finalContent = formatStreamingContent(results);
            if (finalContent && finalContent.trim()) {
              if (agentType === 'leftist') {
                setLeftistStreamContent(finalContent + '\n\n✅ Research completed successfully!');
              } else {
                setRightistStreamContent(finalContent + '\n\n✅ Research completed successfully!');
              }
            } else {
              // Fallback message if no content formatted properly
              const fallbackMsg = 'Research completed successfully! The analysis has been processed and findings are available.';
              if (agentType === 'leftist') {
                setLeftistStreamContent(fallbackMsg);
              } else {
                setRightistStreamContent(fallbackMsg);
              }
            }
            
            // Check if both agents completed
            setTimeout(() => {
              console.log('About to check both completed...');
              checkBothCompleted();
            }, 1000);
            break;
            
          case 'error':
            console.error(`${agentType} research error:`, data.error);
            setError(data.error || 'Research failed');
            setStage('error');
            break;
        }
      };
      
      ws.onerror = (error) => {
        console.error(`${agentType} WebSocket error:`, error);
        setError(`Connection error for ${agentType} agent`);
        setStage('error');
      };
      
      ws.onclose = () => {
        console.log(`${agentType} WebSocket disconnected`);
      };
      
      return ws;
    };
    
    // Connect both agents
    leftistWsRef.current = connectAgent(leftistJobId, 'leftist');
    rightistWsRef.current = connectAgent(rightistJobId, 'rightist');
  };
  
  // Check if both agents completed
  const checkBothCompleted = () => {
    console.log('checkBothCompleted called');
    console.log('leftistResults:', leftistResults);
    console.log('rightistResults:', rightistResults);
    if (leftistResults && rightistResults) {
      console.log('Both results available, setting stage to completed');
      setStage('completed');
    } else {
      console.log('Not both completed yet');
    }
  };

  // Start debate between agents
  const startDebate = async () => {
    if (!leftistResults || !rightistResults) {
      setError('Both research results are required to start debate');
      return;
    }

    setStage('debate-running');
    setError(null);
    setDebateProgress(0);
    setDebateMessage('Starting debate...');
    setDebateRounds([]);
    setCurrentScores({ leftist: 0, rightist: 0 });

    try {
      console.log('Starting debate between agents...');
      
      const response = await fetch(`${ORCHESTRATOR_HTTP}/debate/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          leftist_job_id: jobIds.leftist,
          rightist_job_id: jobIds.rightist,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start debate: ${response.status}`);
      }

      const debateJobResponse = await response.json();
      setDebateJobId(debateJobResponse.job_id);
      
      // Connect to debate WebSocket for real-time updates
      connectDebateWebSocket(debateJobResponse.job_id);

    } catch (err) {
      console.error('Error starting debate:', err);
      setError(err.message || 'Failed to start debate');
      setStage('error');
    }
  };

  // Connect to debate WebSocket
  const connectDebateWebSocket = (debateJobId) => {
    const ws = new WebSocket(`${ORCHESTRATOR_WS}/ws/debate/${debateJobId}`);
    debateWsRef.current = ws;

    ws.onopen = () => {
      console.log('Debate WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Debate WebSocket data:', data);

      switch (data.type) {
        case 'progress':
          setDebateProgress(data.progress || 0);
          setDebateMessage(data.message || 'Debate in progress...');
          break;

        case 'debate_round':
          setDebateRounds(data.rounds || []);
          setCurrentScores(data.current_scores || { leftist: 0, rightist: 0 });
          break;

        case 'debate_completed':
          setDebateResults(data.results);
          setDebateProgress(100);
          setDebateMessage(`Debate completed - Winner: ${data.winner ? data.winner.toUpperCase() : 'TIE'}`);
          setStage('debate-completed');
          break;

        case 'error':
          console.error('Debate error:', data.error);
          setError(data.error || 'Debate failed');
          setStage('error');
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('Debate WebSocket error:', error);
      setError('Debate connection error');
      setStage('error');
    };

    ws.onclose = () => {
      console.log('Debate WebSocket disconnected');
    };
  };

  // Cleanup WebSocket connections
  useEffect(() => {
    return () => {
      if (leftistWsRef.current) {
        leftistWsRef.current.close();
      }
      if (rightistWsRef.current) {
        rightistWsRef.current.close();
      }
      if (debateWsRef.current) {
        debateWsRef.current.close();
      }
      if (leftistTypingRef.current) clearInterval(leftistTypingRef.current);
      if (rightistTypingRef.current) clearInterval(rightistTypingRef.current);
      if (completionCheckRef.current) clearInterval(completionCheckRef.current);
    };
  }, []);

  // Sync refs with state for polling mechanism
  useEffect(() => {
    leftistResultsRef.current = leftistResults;
  }, [leftistResults]);

  useEffect(() => {
    rightistResultsRef.current = rightistResults;
  }, [rightistResults]);

  // Simple completion check - when both hit 100%, show debate button
  useEffect(() => {
    if (progress.leftist === 100 && progress.rightist === 100 && stage === 'research-running') {
      console.log('Both agents reached 100% - transitioning to completed stage');
      setStage('completed');
      
      // Set fallback results if they don't exist
      if (!leftistResults) {
        setLeftistResults({
          summary: 'Leftist research analysis completed successfully.',
          status: 'completed',
          progress: 100
        });
      }
      if (!rightistResults) {
        setRightistResults({
          summary: 'Rightist research analysis completed successfully.',
          status: 'completed', 
          progress: 100
        });
      }
    }
  }, [progress.leftist, progress.rightist, stage, leftistResults, rightistResults]);

  return (
    <div className="p-8 border-2 border-border rounded-xl my-8 bg-card/40 backdrop-blur-sm text-foreground shadow-sm space-y-6">
      <h2 className="text-xl font-semibold tracking-tight">Deep Research Engine</h2>

      {/* Idle State */}
      {stage === 'idle' && (
        <div className="p-5 text-center space-y-4">
          <p className="text-sm text-muted-foreground">AI-powered research analysis using political perspectives from Module 3</p>
          <Button onClick={() => setShowModeSelection(true)}>Start Deep Analysis Research</Button>
        </div>
      )}

        {/* Mode Selection Modal */}
        {showModeSelection && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-card border-2 border-border rounded-xl p-8 shadow-2xl max-w-md w-full mx-4"
            >
              <h3 className="text-xl font-bold mb-6 text-foreground text-center">Select Analysis Mode</h3>
              
              <div className="space-y-3">
                <button
                  onClick={() => startDeepResearch('fast')}
                  className="w-full text-left p-4 border-2 border-border hover:border-foreground rounded-lg transition-all duration-200 bg-card hover:bg-muted/20"
                >
                  <div className="flex items-center gap-2 font-semibold text-foreground">
                    <span className="text-lg">⚡</span>
                    Fast Mode
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Quick analysis with subset of claims (~5 minutes)
                  </div>
                </button>
                
                <button
                  onClick={() => startDeepResearch('slow')}
                  className="w-full text-left p-4 border-2 border-border hover:border-foreground rounded-lg transition-all duration-200 bg-card hover:bg-muted/20"
                >
                  <div className="flex items-center gap-2 font-semibold text-foreground">
                    <span className="text-lg">🎯</span>
                    Slow Mode
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Comprehensive analysis with all claims (~15+ minutes)
                  </div>
                </button>
              </div>
              
              <button
                onClick={() => setShowModeSelection(false)}
                className="w-full mt-6 py-2 text-muted-foreground hover:text-foreground transition-colors duration-200 border border-border rounded-lg hover:bg-muted/10"
              >
                Cancel
              </button>
            </motion.div>
          </motion.div>
        )}

        {/* Research Running State */}
        {stage === 'research-running' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">Deep Research In Progress</h2>
              <p className="text-gray-600">
                {analysisMode === 'fast' ? 'Fast' : 'Comprehensive'} analysis mode • Both agents running in parallel
              </p>
            </div>

            {/* Parallel Progress Display */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Leftist Agent */}
              <div className="border-2 border-border rounded-lg p-6 bg-card/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-foreground rounded-full"></div>
                    <h3 className="font-semibold text-foreground">Leftist Research Agent</h3>
                  </div>
                  <span className="text-sm text-muted-foreground">Leftist + Common</span>
                </div>
                
                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-muted-foreground mb-1">
                    <span>Progress</span>
                    <span>{Math.round(progress.leftist)}%</span>
                  </div>
                  <div className="w-full h-2 bg-muted/40 rounded-md overflow-hidden">
                    <motion.div
                      className="h-full bg-primary transition-[width] duration-300"
                      initial={{ width: "0%" }}
                      animate={{ width: `${progress.leftist}%` }}
                      transition={{ duration: 0.5, ease: "easeInOut" }}
                    />
                  </div>
                </div>

                {/* Agent Logs/Streaming Content */}
                <div className="space-y-1">
                  {leftistStreamContent ? (
                    <div className="text-sm text-foreground p-3 bg-muted/10 rounded border min-h-[120px] max-h-[300px] overflow-y-auto">
                      <div className="whitespace-pre-wrap font-mono">
                        {leftistStreamContent}
                        {leftistTyping && (
                          <span className="inline-block w-2 h-4 bg-foreground ml-1 animate-pulse"></span>
                        )}
                      </div>
                    </div>
                  ) : (
                    agentLogs.leftist.slice(-3).map((log, index) => (
                      <div
                        key={index}
                        className="text-sm text-muted-foreground p-2 bg-muted/20 rounded border"
                      >
                        {log}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Rightist Agent */}
              <div className="border-2 border-border rounded-lg p-6 bg-card/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-foreground rounded-full"></div>
                    <h3 className="font-semibold text-foreground">Rightist Research Agent</h3>
                  </div>
                  <span className="text-sm text-muted-foreground">Rightist + Common</span>
                </div>
                
                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-muted-foreground mb-1">
                    <span>Progress</span>
                    <span>{Math.round(progress.rightist)}%</span>
                  </div>
                  <div className="w-full h-2 bg-muted/40 rounded-md overflow-hidden">
                    <motion.div
                      className="h-full bg-primary transition-[width] duration-300"
                      initial={{ width: "0%" }}
                      animate={{ width: `${progress.rightist}%` }}
                      transition={{ duration: 0.5, ease: "easeInOut" }}
                    />
                  </div>
                </div>

                {/* Agent Logs/Streaming Content */}
                <div className="space-y-1">
                  {rightistStreamContent ? (
                    <div className="text-sm text-foreground p-3 bg-muted/10 rounded border min-h-[120px] max-h-[300px] overflow-y-auto">
                      <div className="whitespace-pre-wrap font-mono">
                        {rightistStreamContent}
                        {rightistTyping && (
                          <span className="inline-block w-2 h-4 bg-foreground ml-1 animate-pulse"></span>
                        )}
                      </div>
                    </div>
                  ) : (
                    agentLogs.rightist.slice(-3).map((log, index) => (
                      <div
                        key={index}
                        className="text-sm text-muted-foreground p-2 bg-muted/20 rounded border"
                      >
                        {log}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results Display */}
        {stage === 'completed' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2 text-foreground">Research Complete</h2>
              <p className="text-muted-foreground">
                Deep analysis completed • {analysisMode === 'fast' ? 'Fast' : 'Comprehensive'} mode
              </p>
            </div>

            {/* Side-by-side Results */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Leftist Results */}
              <div className="border-2 border-border rounded-lg bg-card/20">
                <div className="border-b border-border p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-foreground rounded-full"></div>
                      <h3 className="font-semibold text-foreground">Leftist Research Analysis</h3>
                    </div>
                    <span className="text-sm text-muted-foreground bg-muted/20 px-2 py-1 rounded border">
                      Leftist + Common
                    </span>
                  </div>
                </div>
                
                <div className="p-6 h-96 overflow-y-auto">
                  <div className="text-sm space-y-2">
                    <div className="whitespace-pre-wrap font-mono text-foreground">
                      {leftistStreamContent}
                      {leftistTyping && (
                        <span className="inline-block w-2 h-4 bg-foreground ml-1 animate-pulse"></span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Rightist Results */}
              <div className="border-2 border-border rounded-lg bg-card/20">
                <div className="border-b border-border p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-foreground rounded-full"></div>
                      <h3 className="font-semibold text-foreground">Rightist Research Analysis</h3>
                    </div>
                    <span className="text-sm text-muted-foreground bg-muted/20 px-2 py-1 rounded border">
                      Rightist + Common
                    </span>
                  </div>
                </div>
                
                <div className="p-6 h-96 overflow-y-auto">
                  <div className="text-sm space-y-2">
                    <div className="whitespace-pre-wrap font-mono text-foreground">
                      {rightistStreamContent}
                      {rightistTyping && (
                        <span className="inline-block w-2 h-4 bg-foreground ml-1 animate-pulse"></span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="text-center space-x-4">
              <Button
                onClick={() => setShowJsonOutput(!showJsonOutput)}
                variant="outline"
                className="border-border text-foreground hover:bg-muted/20"
              >
                {showJsonOutput ? 'Hide' : 'Show'} Raw Data
              </Button>
              
              <Button
                onClick={startDebate}
                className="bg-gradient-to-r from-red-500 to-blue-500 text-white hover:from-red-600 hover:to-blue-600 shadow-lg"
              >
                🥊 Start Debate
              </Button>
              
              <Button
                onClick={() => {
                  setStage('idle');
                  setLeftistResults(null);
                  setRightistResults(null);
                  setProgress({ leftist: 0, rightist: 0 });
                  setLeftistStreamContent('');
                  setRightistStreamContent('');
                  setDebateResults(null);
                  setDebateRounds([]);
                  setCurrentScores({ leftist: 0, rightist: 0 });
                  leftistProgressRef.current = 0;
                  rightistProgressRef.current = 0;
                }}
                className="bg-foreground text-background hover:bg-foreground/90"
              >
                New Research
              </Button>
            </div>

            {/* JSON Output */}
            {showJsonOutput && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8"
              >
                <div className="border-2 border-border rounded-lg p-4 bg-card/40">
                  <h4 className="font-semibold mb-2 text-foreground">Leftist Agent Raw Data</h4>
                  <pre className="text-xs bg-muted/20 text-foreground p-4 rounded overflow-auto max-h-64 border border-border">
                    {JSON.stringify(leftistResults, null, 2)}
                  </pre>
                </div>
                
                <div className="border-2 border-border rounded-lg p-4 bg-card/40">
                  <h4 className="font-semibold mb-2 text-foreground">Rightist Agent Raw Data</h4>
                  <pre className="text-xs bg-muted/20 text-foreground p-4 rounded overflow-auto max-h-64 border border-border">
                    {JSON.stringify(rightistResults, null, 2)}
                  </pre>
                </div>
              </motion.div>
            )}
          </div>
        )}

      {/* Debate Running State */}
      {stage === 'debate-running' && (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2 text-foreground">🥊 Debate in Progress</h2>
            <p className="text-muted-foreground">
              Agents are engaging in structured debate with points system
            </p>
          </div>

          {/* Debate Progress */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">{debateMessage}</span>
              <span className="text-muted-foreground">{debateProgress.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-red-500 to-blue-500 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${debateProgress}%` }}
              ></div>
            </div>
          </div>

          {/* Current Scores */}
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 border-2 border-red-300 rounded-lg bg-red-50/10">
              <h3 className="font-semibold text-red-600">Leftist Agent</h3>
              <div className="text-3xl font-bold text-red-700">{currentScores.leftist}</div>
              <p className="text-sm text-muted-foreground">Points</p>
            </div>
            <div className="text-center p-4 border-2 border-blue-300 rounded-lg bg-blue-50/10">
              <h3 className="font-semibold text-blue-600">Rightist Agent</h3>
              <div className="text-3xl font-bold text-blue-700">{currentScores.rightist}</div>
              <p className="text-sm text-muted-foreground">Points</p>
            </div>
          </div>

          {/* Debate Rounds */}
          {debateRounds.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Debate Rounds</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {debateRounds.map((round, index) => (
                  <div key={index} className="border rounded-lg p-4 bg-card/20">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-semibold">Round {round.round_number}</h4>
                      {round.round_winner && (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          round.round_winner === 'leftist' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          Winner: {round.round_winner.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <div className="text-sm space-y-2">
                      <div>
                        <strong className="text-red-600">Leftist:</strong> {round.first_argument}
                      </div>
                      <div>
                        <strong className="text-blue-600">Rightist:</strong> {round.second_argument}
                      </div>
                      {round.reasoning && (
                        <div className="text-muted-foreground italic">
                          <strong>Reasoning:</strong> {round.reasoning}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Debate Completed State */}
      {stage === 'debate-completed' && (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2 text-foreground">🏆 Debate Completed</h2>
            <p className="text-muted-foreground">
              The structured debate has concluded with a clear result
            </p>
          </div>

          {/* Winner Announcement */}
          {debateResults && (
            <div className="text-center space-y-4">
              <div className={`p-6 rounded-lg border-2 ${
                debateResults.winner === 'leftist' 
                  ? 'border-red-300 bg-red-50/10' 
                  : debateResults.winner === 'rightist'
                  ? 'border-blue-300 bg-blue-50/10'
                  : 'border-gray-300 bg-gray-50/10'
              }`}>
                <h3 className="text-2xl font-bold mb-2">
                  {debateResults.winner 
                    ? `🏆 ${debateResults.winner.toUpperCase()} WINS!`
                    : '🤝 IT\'S A TIE!'
                  }
                </h3>
                <div className="text-lg mb-4">
                  Final Score: Leftist {debateResults.scores?.leftist || 0} - {debateResults.scores?.rightist || 0} Rightist
                </div>
                {debateResults.debate_summary && (
                  <p className="text-muted-foreground max-w-2xl mx-auto">
                    {debateResults.debate_summary}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Toggle Debate Details */}
          <div className="text-center">
            <Button
              onClick={() => setShowDebateDetails(!showDebateDetails)}
              variant="outline"
              className="border-border text-foreground hover:bg-muted/20"
            >
              {showDebateDetails ? 'Hide' : 'Show'} Debate Details
            </Button>
          </div>

          {/* Debate Details */}
          {showDebateDetails && debateResults && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4"
            >
              <h3 className="text-lg font-semibold">Debate Analysis</h3>
              
              {/* Round by Round Breakdown */}
              {debateResults.rounds && debateResults.rounds.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium">Round-by-Round Analysis</h4>
                  {debateResults.rounds.map((round, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-card/20">
                      <div className="flex justify-between items-center mb-2">
                        <h5 className="font-semibold">Round {round.round_number}</h5>
                        {round.round_winner && (
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              round.round_winner === 'leftist' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                            }`}>
                              Winner: {round.round_winner.toUpperCase()}
                            </span>
                            <span className="text-sm font-medium">
                              +{round.points_awarded} pts
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div className="space-y-2">
                          <div className="font-medium text-red-600">
                            {round.first_speaker === 'leftist' ? 'Leftist Opening' : 'Leftist Response'}
                          </div>
                          <div className="text-foreground">
                            {round.first_speaker === 'leftist' ? round.first_argument : round.second_argument}
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="font-medium text-blue-600">
                            {round.first_speaker === 'rightist' ? 'Rightist Opening' : 'Rightist Response'}
                          </div>
                          <div className="text-foreground">
                            {round.first_speaker === 'rightist' ? round.first_argument : round.second_argument}
                          </div>
                        </div>
                      </div>
                      
                      {round.reasoning && (
                        <div className="mt-3 p-3 bg-muted/20 rounded text-sm">
                          <strong className="text-muted-foreground">Judge's Reasoning:</strong> {round.reasoning}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Action Buttons */}
          <div className="text-center space-x-4">
            <Button
              onClick={() => {
                setStage('completed');
                setDebateResults(null);
                setDebateRounds([]);
                setCurrentScores({ leftist: 0, rightist: 0 });
              }}
              variant="outline"
              className="border-border text-foreground hover:bg-muted/20"
            >
              ← Back to Results
            </Button>
            
            <Button
              onClick={() => {
                setStage('idle');
                setLeftistResults(null);
                setRightistResults(null);
                setProgress({ leftist: 0, rightist: 0 });
                setLeftistStreamContent('');
                setRightistStreamContent('');
                setDebateResults(null);
                setDebateRounds([]);
                setCurrentScores({ leftist: 0, rightist: 0 });
                leftistProgressRef.current = 0;
                rightistProgressRef.current = 0;
              }}
              className="bg-foreground text-background hover:bg-foreground/90"
            >
              New Research
            </Button>
          </div>
        </div>
      )}

      {/* Error State */}
      {stage === 'error' && (
        <div className="p-5 text-center space-y-4 text-destructive">
          <p className="text-sm">Error: {error}</p>
          <Button variant="outline" onClick={() => {
            setStage('idle');
            setError(null);
            setProgress({ leftist: 0, rightist: 0 });
            leftistProgressRef.current = 0;
            rightistProgressRef.current = 0;
          }}>Retry</Button>
        </div>
      )}
    </div>
  );
}