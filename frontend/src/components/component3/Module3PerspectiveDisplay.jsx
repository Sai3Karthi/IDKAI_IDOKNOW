import React, { useState, useEffect, useRef } from 'react';
import { PoliticalSpectrumChart } from './PoliticalSpectrumChart';

// Environment-driven orchestrator port (falls back to 8001)
const ORCHESTRATOR_PORT = process.env.REACT_APP_ORCHESTRATOR_PORT || 8000;
const ORCH_HTTP = `http://localhost:${ORCHESTRATOR_PORT}`;

/**
 * Module3PerspectiveDisplay component
 * Loads the module3 perspective data and displays it using the PoliticalSpectrumChart
 */
export function Module3PerspectiveDisplay({ topic = "PM Modi on nepal's new constitution" }) {
  const [data, setData] = useState({ leftist: [], rightist: [], common: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const pollingRef = useRef(null);
  
  // Check pipeline status and load data when ready
  useEffect(() => {
    async function checkPipelineStatus() {
      try {
        const response = await fetch(`${ORCH_HTTP}/status`);
        if (!response.ok) {
          console.error('Failed to fetch pipeline status');
          return false;
        }
        
        const status = await response.json();
        setPipelineStatus(status);
        
        // If pipeline is done or idle, we can try to load data
        return status.stage === 'done' || status.stage === 'idle' || status.stage === 'error';
      } catch (err) {
        console.error('Error checking pipeline status:', err);
        return false;
      }
    }
    
    async function loadData() {
      try {
        setLoading(true);
        
        // First check if pipeline is complete before loading data
        const isReady = await checkPipelineStatus();
        
        if (!isReady) {
          // Pipeline still running, set up polling and return early
          if (!pollingRef.current) {
            console.log('Pipeline still running, setting up polling');
            pollingRef.current = setInterval(async () => {
              const ready = await checkPipelineStatus();
              if (ready) {
                console.log('Pipeline complete, loading data');
                clearInterval(pollingRef.current);
                pollingRef.current = null;
                loadData();
              }
            }, 2000); // Poll every 2 seconds
          }
          return;
        }
        
        // Fetch all three data sources
        const responses = await Promise.all([
          fetch(`${ORCH_HTTP}/module3/output/leftist`),
          fetch(`${ORCH_HTTP}/module3/output/rightist`),
          fetch(`${ORCH_HTTP}/module3/output/common`)
        ]);
        
        // Check for any errors
        for (const [index, response] of responses.entries()) {
          if (!response.ok) {
            // If we get a 409 Conflict (pipeline running), set up polling
            if (response.status === 409) {
              const errorData = await response.json();
              console.log('Pipeline still running:', errorData);
              
              if (!pollingRef.current) {
                console.log('Setting up polling for pipeline completion');
                pollingRef.current = setInterval(async () => {
                  const ready = await checkPipelineStatus();
                  if (ready) {
                    console.log('Pipeline complete, loading data');
                    clearInterval(pollingRef.current);
                    pollingRef.current = null;
                    loadData();
                  }
                }, 2000); // Poll every 2 seconds
              }
              
              setError(`Pipeline is still running (${errorData.stage}, ${errorData.progress}%). Please wait for it to complete.`);
              setLoading(false);
              return;
            } else {
              throw new Error(`Failed to fetch module3 data (${['leftist', 'rightist', 'common'][index]}: ${response.status})`);
            }
          }
        }
        
        // Parse JSON responses
        const [leftistData, rightistData, commonData] = await Promise.all(
          responses.map(r => r.json())
        );
        
        // Update state with fetched data
        setData({
          leftist: leftistData || [],
          rightist: rightistData || [],
          common: commonData || []
        });
        
        setLoading(false);
        setError(null);
      } catch (err) {
        console.error('Error loading module3 data:', err);
        setError(err.message);
        setLoading(false);
      }
    }
    
    loadData();
    
    // Clean up polling on unmount
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);
  
  // Handle hover on data points
  const handlePointHover = (point) => {
    // Could implement additional functionality when hovering on points
    // console.log('Hovered point:', point);
  };
  
  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
          <div className="mt-4 text-sm text-muted-foreground">
            {pipelineStatus && pipelineStatus.stage !== "done" && pipelineStatus.stage !== "idle" 
              ? `Pipeline in progress (${pipelineStatus.stage}, ${pipelineStatus.progress}%)...` 
              : "Loading perspective data..."}
          </div>
          {pipelineStatus && pipelineStatus.stage !== "done" && pipelineStatus.stage !== "idle" && (
            <div className="mt-4 w-64 h-2 bg-muted/40 rounded-md overflow-hidden">
              <div
                className="h-full bg-primary transition-[width] duration-300"
                style={{ width: `${pipelineStatus.progress || 0}%` }}
              />
            </div>
          )}
        </div>
      </div>
    );
  }
  
  // Handler to manually retry loading data
  const handleRetry = () => {
    setLoading(true);
    setError(null);
    
    // Force a reload by clearing any polling interval and starting fresh
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    
    // Check status and load data
    async function reloadData() {
      try {
        const response = await fetch(`${ORCH_HTTP}/status`);
        if (response.ok) {
          const status = await response.json();
          setPipelineStatus(status);
          
          // If pipeline is done, try loading data
          if (status.stage === 'done' || status.stage === 'idle' || status.stage === 'error') {
            // Fetch all three data sources
            const responses = await Promise.all([
              fetch(`${ORCH_HTTP}/module3/output/leftist`),
              fetch(`${ORCH_HTTP}/module3/output/rightist`),
              fetch(`${ORCH_HTTP}/module3/output/common`)
            ]);
            
            // Check for any errors
            if (!responses.every(r => r.ok)) {
              throw new Error('Failed to fetch module3 data');
            }
            
            // Parse JSON responses
            const [leftistData, rightistData, commonData] = await Promise.all(
              responses.map(r => r.json())
            );
            
            // Update state with fetched data
            setData({
              leftist: leftistData || [],
              rightist: rightistData || [],
              common: commonData || []
            });
            
            setLoading(false);
          } else {
            // Pipeline still running, show error
            setError(`Pipeline is still running (${status.stage}, ${status.progress}%). Please wait for it to complete.`);
            setLoading(false);
          }
        } else {
          throw new Error('Failed to check pipeline status');
        }
      } catch (err) {
        console.error('Error reloading data:', err);
        setError(err.message);
        setLoading(false);
      }
    }
    
    reloadData();
  };

  if (error) {
    // Check if the error is related to a pipeline in progress
    const isPipelineRunning = error.includes('Pipeline is still running');
    
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <div className={isPipelineRunning ? "text-amber-600" : "text-destructive"}>
          <div className="font-semibold">{isPipelineRunning ? "Pipeline in Progress" : "Error loading perspective data"}</div>
          <div className="text-sm mt-2">{error}</div>
          {isPipelineRunning && pipelineStatus && (
            <div className="mt-4 space-y-2">
              <div className="w-full h-2 bg-muted/40 rounded-md overflow-hidden">
                <div
                  className="h-full bg-amber-500 transition-[width] duration-300"
                  style={{ width: `${pipelineStatus.progress || 0}%` }}
                />
              </div>
              <div className="text-xs text-muted-foreground">
                Current stage: <span className="font-medium">{pipelineStatus.stage}</span>
              </div>
            </div>
          )}
          <div className="mt-4 text-xs text-muted-foreground">
            {isPipelineRunning 
              ? "Waiting for the current pipeline to complete before showing latest results..." 
              : "Make sure the orchestrator server is running and module3 has been executed."}
          </div>
          <div className="mt-4">
            <button
              onClick={handleRetry}
              className="px-3 py-1 text-xs font-medium bg-primary/80 hover:bg-primary text-white rounded-md transition-colors"
            >
              {isPipelineRunning ? "Check Again" : "Retry"}
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  const totalPoints = data.leftist.length + data.rightist.length + data.common.length;
  
  return (
    <div className="w-full">
      <div className="mb-6 relative">
        <PoliticalSpectrumChart 
          data={data} 
          title={`Political Spectrum Visualization for: "${topic}"`}
          height={500}
          onPointHover={handlePointHover}
        />
        
        {/* Reload button positioned in top-left corner with better spacing */}
        <button
          onClick={handleRetry}
          className="absolute top-4 left-4 px-2.5 py-1.5 text-xs font-medium bg-card/90 hover:bg-card border border-border/60 rounded-md shadow-sm transition-colors flex items-center gap-1.5"
          title="Reload latest data"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2v6h-6"></path>
            <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
            <path d="M3 22v-6h6"></path>
            <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
          </svg>
          <span>Reload</span>
        </button>
      </div>
      
      <div className="text-sm text-muted-foreground">
        <div className="flex justify-between">
          <span>Total perspectives: {totalPoints}</span>
          <span className="flex gap-x-6">
            <span>Leftist: {data.leftist.length}</span>
            <span>Common: {data.common.length}</span>
            <span>Rightist: {data.rightist.length}</span>
          </span>
        </div>
      </div>
    </div>
  );
}

export default Module3PerspectiveDisplay;