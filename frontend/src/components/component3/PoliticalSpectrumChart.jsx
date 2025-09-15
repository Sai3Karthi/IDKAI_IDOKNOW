import React, { useMemo, useRef, useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';

// Color mapping from the existing component, keeping for consistency
const COLOR_MAP = {
  red: '#ff5f6d',
  orange: '#ff8008',
  yellow: '#f7971e',
  green: '#38ef7d',
  blue: '#396afc',
  indigo: '#4776e6',
  violet: '#7f00ff',
  purple: '#6441A5',
  teal: '#136a8a'
};

// Background zone colors based on the provided image
const ZONE_COLORS = {
  leftist: 'rgba(96, 60, 60, 0.7)',      // Darker red/brown for leftist zone (matches screenshot)
  common: 'rgba(60, 96, 70, 0.7)',       // Darker green for common/center zone (matches screenshot)
  rightist: 'rgba(70, 60, 96, 0.7)'      // Darker purple for rightist zone (matches screenshot)
};

/**
 * PoliticalSpectrumChart
 * Visualization for module3's political spectrum data
 * - Shows bias on X axis and significance on Y axis
 * - Color-coded background zones for leftist, center, and rightist areas
 * - Animated data points with color coding
 * - Based on the StreamingBiasSignificanceMotionChart
 */
export function PoliticalSpectrumChart({
  data = { leftist: [], rightist: [], common: [] },
  title = "Political Spectrum Visualization",
  xDomain = [0, 1],
  yDomain = [0, 1],
  height = 400,
  margin = { top: 40, right: 28, bottom: 48, left: 56 },
  animateAxis = true,
  onPointHover
}) {
  const containerRef = useRef(null);
  const [width, setWidth] = useState(640);
  const [hovered, setHovered] = useState(null);
  const [hiddenCategories, setHiddenCategories] = useState(new Set());
  const svgRef = useRef(null);
  const [readyForPoints, setReadyForPoints] = useState(false);
  
  // Zone boundary values (matching the image)
  const leftBoundary = 0.36;   // Where leftist zone ends
  const rightBoundary = 0.64;  // Where rightist zone begins
  
  // Toggle visibility of categories
  const toggleCategory = useCallback((category) => {
    setHiddenCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category); else next.add(category);
      return next;
    });
  }, []);

  // Delay points to let users watch axis build: axis duration ~2.2s + tick fade => show points after 1.4s
  useEffect(() => {
    const t = setTimeout(() => setReadyForPoints(true), 1400);
    return () => clearTimeout(t);
  }, []);

  // Resize observer for responsive width
  useEffect(() => {
    const ro = new ResizeObserver(entries => {
      for (const e of entries) setWidth(e.contentRect.width);
    });
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Flatten all data points for rendering
  const points = useMemo(() => {
    const flat = [];
    
    // Helper function to ensure proper point distribution
    const normalizePoint = (p, category) => {
      let bias_x = p.bias_x;
      
      // Make sure leftist points are properly in the leftist zone
      if (category === 'leftist' && bias_x > leftBoundary * 0.9) {
        bias_x = Math.max(0, Math.min(leftBoundary * 0.98, bias_x));
      }
      // Make sure rightist points are properly in the rightist zone
      else if (category === 'rightist' && bias_x < rightBoundary * 1.1) {
        bias_x = Math.max(rightBoundary * 1.02, Math.min(1, bias_x));
      }
      // Make sure common points are in the common zone
      else if (category === 'common') {
        bias_x = Math.max(leftBoundary * 1.02, Math.min(rightBoundary * 0.98, bias_x));
      }
      
      // Add jitter to prevent overlap - calculate a small random offset
      // but ensure it keeps the point within its proper zone
      const jitterX = category === 'leftist' 
        ? (Math.random() - 0.5) * 0.08 
        : category === 'rightist' 
          ? (Math.random() - 0.5) * 0.08 
          : (Math.random() - 0.5) * 0.05;
          
      const jitterY = (Math.random() - 0.5) * 0.05;
      
      // Ensure bias_x stays within zone boundaries after jitter
      const finalBiasX = Math.max(
        category === 'leftist' ? 0 : category === 'common' ? leftBoundary : rightBoundary,
        Math.min(
          category === 'leftist' ? leftBoundary * 0.95 : category === 'common' ? rightBoundary * 0.95 : 1,
          bias_x + jitterX
        )
      );
      
      // Ensure significance_y stays within valid bounds after jitter
      const finalSignificanceY = Math.max(0, Math.min(1, p.significance_y + jitterY));
      
      return {
        ...p,
        bias_x: finalBiasX,
        significance_y: finalSignificanceY,
        id: p.id || p.text || `${category}-${Math.random().toString(36).slice(2)}`,
        category
      };
    };
    
    // Add category identifier to each point and normalize distribution
    if (!hiddenCategories.has('leftist')) {
      data.leftist?.forEach(p => {
        flat.push(normalizePoint(p, 'leftist'));
      });
    }
    
    if (!hiddenCategories.has('common')) {
      data.common?.forEach(p => {
        flat.push(normalizePoint(p, 'common'));
      });
    }
    
    if (!hiddenCategories.has('rightist')) {
      data.rightist?.forEach(p => {
        flat.push(normalizePoint(p, 'rightist'));
      });
    }
    
    return flat;
  }, [data, hiddenCategories, leftBoundary, rightBoundary]);

  // Scaling functions
  const innerW = Math.max(0, width - margin.left - margin.right);
  const innerH = Math.max(0, height - margin.top - margin.bottom);

  const xScale = v => margin.left + ((v - xDomain[0]) / (xDomain[1] - xDomain[0] || 1)) * innerW;
  const yScale = v => margin.top + innerH - ((v - yDomain[0]) / (yDomain[1] - yDomain[0] || 1)) * innerH;
  
  // Zone boundaries in pixels
  const leftBoundaryPx = xScale(leftBoundary);
  const rightBoundaryPx = xScale(rightBoundary);

  // Tick generator
  const genTicks = (min, max, count = 6) => {
    if (min === max) return [min];
    const step = (max - min) / count;
    return Array.from({ length: count + 1 }, (_, i) => +(min + i * step).toFixed(2));
  };
  const xTicks = genTicks(xDomain[0], xDomain[1], 6);
  const yTicks = genTicks(yDomain[0], yDomain[1], 6);

  // Slower axis animation for more pronounced build
  const axisAnim = (delay = 0) => animateAxis ? { 
    initial: { pathLength: 0 }, 
    animate: { pathLength: 1, transition: { duration: 2.2, delay, ease: 'easeInOut' } }
  } : {};

  return (
    <div ref={containerRef} style={{ width: '100%', height }} className="relative select-none">
      {/* Title */}
      <motion.div 
        className="absolute top-1 left-1/2 transform -translate-x-1/2 font-semibold text-sm z-10"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {title}
      </motion.div>
      
      {/* Legend */}
      <div className="absolute top-1 right-2 z-10 flex flex-wrap gap-2 text-[10px]">
        <button 
          onClick={() => toggleCategory('leftist')}
          className={`px-2 py-1 rounded-md border backdrop-blur-sm transition text-foreground/90 ${hiddenCategories.has('leftist') ? 'opacity-40 line-through' : 'opacity-90'} hover:opacity-100`}
          style={{ background: '#ff5f6d22', borderColor: '#ff5f6d55' }}>
          Leftist
        </button>
        <button 
          onClick={() => toggleCategory('common')}
          className={`px-2 py-1 rounded-md border backdrop-blur-sm transition text-foreground/90 ${hiddenCategories.has('common') ? 'opacity-40 line-through' : 'opacity-90'} hover:opacity-100`}
          style={{ background: '#38ef7d22', borderColor: '#38ef7d55' }}>
          Common
        </button>
        <button 
          onClick={() => toggleCategory('rightist')}
          className={`px-2 py-1 rounded-md border backdrop-blur-sm transition text-foreground/90 ${hiddenCategories.has('rightist') ? 'opacity-40 line-through' : 'opacity-90'} hover:opacity-100`}
          style={{ background: '#7f00ff22', borderColor: '#7f00ff55' }}>
          Rightist
        </button>
      </div>
      
      <svg ref={svgRef} width={width} height={height} className="overflow-visible">
        <LayoutGroup>
          {/* Background zones */}
          <g opacity={0.9}>
            {/* Leftist zone */}
            <rect 
              x={margin.left} 
              y={margin.top} 
              width={leftBoundaryPx - margin.left} 
              height={innerH} 
              fill={ZONE_COLORS.leftist}
              opacity={hiddenCategories.has('leftist') ? 0.3 : 1}
            />
            
            {/* Common zone */}
            <rect 
              x={leftBoundaryPx} 
              y={margin.top} 
              width={rightBoundaryPx - leftBoundaryPx} 
              height={innerH} 
              fill={ZONE_COLORS.common}
              opacity={hiddenCategories.has('common') ? 0.3 : 1}
            />
            
            {/* Rightist zone */}
            <rect 
              x={rightBoundaryPx} 
              y={margin.top} 
              width={margin.left + innerW - rightBoundaryPx} 
              height={innerH} 
              fill={ZONE_COLORS.rightist}
              opacity={hiddenCategories.has('rightist') ? 0.3 : 1}
            />
          </g>

          {/* Zone labels */}
          <motion.text 
            x={xScale(0.18)} 
            y={margin.top + 16} 
            textAnchor="middle" 
            fontSize={12} 
            fill="rgba(255,95,109,0.8)"
            initial={{ opacity: 0 }}
            animate={{ opacity: hiddenCategories.has('leftist') ? 0.3 : 0.8 }}
            transition={{ delay: 1.8 }}
          >
            Leftist Zone
          </motion.text>
          
          <motion.text 
            x={xScale(0.5)} 
            y={margin.top + 16} 
            textAnchor="middle" 
            fontSize={12} 
            fill="rgba(56,239,125,0.8)"
            initial={{ opacity: 0 }}
            animate={{ opacity: hiddenCategories.has('common') ? 0.3 : 0.8 }}
            transition={{ delay: 1.9 }}
          >
            Common Zone
          </motion.text>
          
          <motion.text 
            x={xScale(0.82)} 
            y={margin.top + 16} 
            textAnchor="middle" 
            fontSize={12} 
            fill="rgba(127,0,255,0.8)"
            initial={{ opacity: 0 }}
            animate={{ opacity: hiddenCategories.has('rightist') ? 0.3 : 0.8 }}
            transition={{ delay: 2.0 }}
          >
            Rightist Zone
          </motion.text>

          {/* Axes */}
          <motion.line
            key="x-axis"
            x1={margin.left}
            y1={margin.top + innerH}
            x2={margin.left + innerW}
            y2={margin.top + innerH}
            stroke="hsl(var(--foreground)/0.9)"
            strokeWidth={2}
            shapeRendering="crispEdges"
            {...axisAnim(0.05)}
          />
          <motion.line
            key="y-axis"
            x1={margin.left}
            y1={margin.top}
            x2={margin.left}
            y2={margin.top + innerH}
            stroke="hsl(var(--foreground)/0.9)"
            strokeWidth={2}
            shapeRendering="crispEdges"
            {...axisAnim(0.15)}
          />

          {/* X ticks */}
          {xTicks.map((t, i) => {
            const x = xScale(t);
            return (
              <motion.g key={`xt-${t}`} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .55 + i * .07 }}>
                <line x1={x} x2={x} y1={margin.top + innerH} y2={margin.top + innerH + 6} stroke="hsl(var(--border)/0.7)" />
                <text x={x} y={margin.top + innerH + 18} textAnchor="middle" fontSize={11} fill="hsl(var(--foreground)/0.85)" fontWeight="500">{t}</text>
              </motion.g>
            );
          })}

          {/* Y ticks */}
          {yTicks.map((t, i) => {
            const y = yScale(t);
            return (
              <motion.g key={`yt-${t}`} initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: .55 + i * .07 }}>
                <line x1={margin.left - 6} x2={margin.left} y1={y} y2={y} stroke="hsl(var(--border)/0.7)" />
                <text x={margin.left - 10} y={y + 3} textAnchor="end" fontSize={11} fill="hsl(var(--foreground)/0.85)" fontWeight="500">{t}</text>
              </motion.g>
            );
          })}
          
          {/* Zone dividing lines (vertical) */}
          <motion.line
            x1={leftBoundaryPx}
            y1={margin.top}
            x2={leftBoundaryPx}
            y2={margin.top + innerH}
            stroke="rgba(150,150,150,0.5)"
            strokeWidth={1}
            strokeDasharray="4 2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.2 }}
          />
          
          <motion.line
            x1={rightBoundaryPx}
            y1={margin.top}
            x2={rightBoundaryPx}
            y2={margin.top + innerH}
            stroke="rgba(150,150,150,0.5)"
            strokeWidth={1}
            strokeDasharray="4 2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.2 }}
          />

          {/* Points */}
          <AnimatePresence>
            {readyForPoints && points.map(p => {
              // Determine color based on both the data color and the category
              let baseColor;
              if (p.category === 'leftist') {
                baseColor = COLOR_MAP.red;
                if (p.color === 'orange') baseColor = COLOR_MAP.orange;
                else if (p.color === 'yellow') baseColor = COLOR_MAP.yellow;
              } else if (p.category === 'common') {
                baseColor = COLOR_MAP.green;
                if (p.color === 'yellow') baseColor = COLOR_MAP.yellow;
                else if (p.color === 'blue') baseColor = COLOR_MAP.blue;
              } else { // rightist
                baseColor = COLOR_MAP.violet;
                if (p.color === 'blue') baseColor = COLOR_MAP.blue;
                else if (p.color === 'indigo') baseColor = COLOR_MAP.indigo;
              }
              
              // Fallback if no color was assigned
              if (!baseColor) {
                baseColor = COLOR_MAP[p.color] || '#999';
              }
              
              return (
                <motion.circle
                  key={p.id}
                  cx={xScale(p.bias_x)}
                  cy={yScale(p.significance_y)}
                  r={7} // Slightly larger for better visibility
                  initial="hidden"
                  animate={{ 
                    opacity: 1, 
                    scale: [0, 1.55, 1], 
                    transition: { 
                      duration: 1.25, 
                      ease: 'easeOut',
                      // Stagger the points based on category
                      delay: 0.05 + (p.category === 'leftist' ? 0 : p.category === 'common' ? 0.3 : 0.6) + Math.random() * 0.3
                    } 
                  }}
                  strokeWidth={2}
                  fill={baseColor + 'AA'} // More opaque fill
                  style={{ 
                    cursor: 'pointer', 
                    filter: hovered?.id === p.id ? 'drop-shadow(0 0 6px rgba(255,255,255,.8))' : 'none' 
                  }}
                  whileHover={{ scale: 1.4 }}
                  onMouseEnter={() => { 
                    setHovered(p); 
                    onPointHover && onPointHover(p); 
                  }}
                  onMouseLeave={() => setHovered(h => h === p ? null : h)}
                  stroke={baseColor}
                />
              );
            })}
          </AnimatePresence>
        </LayoutGroup>
      </svg>

      {/* Axis labels */}
      <motion.div className="absolute left-1/2 -translate-x-1/2 bottom-1 text-[12px] text-foreground"
        initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0, transition: { delay: 1.3 } }}>
        Bias (Left &lt; {leftBoundary} | Center | Right &gt; {rightBoundary})
      </motion.div>
      <motion.div className="absolute top-1/2 left-2 text-[12px] text-foreground" style={{ writingMode: 'vertical-rl', transform: 'translateY(-55%) rotate(180deg)' }}
        initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0, transition: { delay: 1.45 } }}>
        Significance
      </motion.div>

      {/* Tooltip */}
      <AnimatePresence>
        {hovered && (
          <motion.div
            className="pointer-events-none absolute rounded-md bg-popover/90 backdrop-blur px-2 py-1 text-[11px] leading-snug border border-border shadow-md max-w-[240px] z-20"
            initial={{ opacity: 0, scale: .9, y: 4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: .9, y: 4, transition: { duration: 0.15 } }}
            style={{ 
              left: xScale(hovered.bias_x) + 10, 
              top: yScale(hovered.significance_y) - 10 
            }}
          >
            <div className="font-medium mb-0.5 capitalize">{hovered.category} - {hovered.color}</div>
            <div className="opacity-80">Bias {hovered.bias_x.toFixed(2)} | Sig {hovered.significance_y.toFixed(2)}</div>
            {hovered.text && <div className="mt-0.5 line-clamp-3">{hovered.text}</div>}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      {!points.length && (
        <div className="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground/70 italic">
          No data points available
        </div>
      )}
    </div>
  );
}

export default PoliticalSpectrumChart;