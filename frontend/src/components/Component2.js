import React from 'react';
import MisinformationAnalyzer from './component2/Component2';

export default function Component2({ scrapedContent, onClearScrapedContent }) {
  return <MisinformationAnalyzer scrapedContent={scrapedContent} onClearScrapedContent={onClearScrapedContent} />;
}
