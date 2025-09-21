import React, { useState } from 'react';
import Component1 from './components/Component1';
import Component2 from './components/Component2';
import { Component3 } from './components/component3';
import Component4 from './components/component4/Component4';
import { BackgroundRippleEffect } from './components/ui/background-ripple-effect';

function App() {
  // Shared state for scraped content from URL validation
  const [scrapedContent, setScrapedContent] = useState(null);

  const handleScrapedContent = (content, sourceUrl) => {
    setScrapedContent({
      content,
      sourceUrl,
      timestamp: new Date().toISOString(),
      id: Date.now()
    });
  };

  const clearScrapedContent = () => {
    setScrapedContent(null);
  };

  return (
  <div className="relative min-h-screen w-full text-foreground bg-background px-4 md:px-8 py-10">
      <BackgroundRippleEffect className="z-0" />
      <div className="relative z-10 space-y-8">
        <header className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">IDK-IDoKnow Frontend</h1>
          <p className="text-sm text-muted-foreground">Edit <code className="px-1.5 py-0.5 rounded border bg-card/40">src/App.js</code> and save to reload.</p>
        </header>
        <div className="flex flex-col gap-8">
          <div className="w-full">
            <Component1 onScrapedContent={handleScrapedContent} />
          </div>
          <div className="w-full">
            <Component2 
              scrapedContent={scrapedContent} 
              onClearScrapedContent={clearScrapedContent}
            />
          </div>
          <div className="w-full">
            <Component3 />
          </div>
          <div className="w-full">
            <Component4 />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
