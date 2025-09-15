"use client";
import React, { useEffect, useId, useState, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import { cn } from "../../lib/utils";
import { SparklesCore } from "./sparkles";

export const Cover = ({
  children,
  className,
  autoPlay = false,
  autoPlayDelay = 5500 // Default delay of 5.5 seconds
}) => {
  const [hovered, setHovered] = useState(false);
  const [animationPhase, setAnimationPhase] = useState("initial"); // initial, animating, completed
  const [displayText, setDisplayText] = useState(children);
  
  const ref = useRef(null);
 
  const [containerWidth, setContainerWidth] = useState(0);
  const [beamPositions, setBeamPositions] = useState([]);
 
  // Initialize beam positions and container width
  useEffect(() => {
    if (ref.current) {
      setContainerWidth(ref.current?.clientWidth ?? 0);
 
      const height = ref.current?.clientHeight ?? 0;
      const numberOfBeams = Math.floor(height / 10); // Adjust the divisor to control the spacing
      const positions = Array.from(
        { length: numberOfBeams },
        (_, i) => (i + 1) * (height / (numberOfBeams + 1))
      );
      setBeamPositions(positions);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Update display text whenever children prop changes
  useEffect(() => {
    if (animationPhase !== "completed") {
      setDisplayText(children);
    }
  }, [children, animationPhase]);

  // Auto-play animation effect
  useEffect(() => {
    let autoPlayTimer;
    let autoPlayDuration;
    let textChangeTimer;
    
    if (autoPlay) {
      // Start the auto-play after the specified delay
      autoPlayTimer = setTimeout(() => {
        setHovered(true);
        setAnimationPhase("animating");
        
        // Keep the animation visible for 4 seconds exactly
        autoPlayDuration = setTimeout(() => {
          setHovered(false);
          
          // Change text and keep it visible
          textChangeTimer = setTimeout(() => {
            setDisplayText("All cleaned and distributed");
            setAnimationPhase("completed");
            // Keep the component visible but without animation effects
            setHovered(false);
          }, 300); // Small delay after animation ends for smooth transition
        }, 4000);
      }, autoPlayDelay);
    }
    
    return () => {
      clearTimeout(autoPlayTimer);
      clearTimeout(autoPlayDuration);
      clearTimeout(textChangeTimer);
    };
  }, [autoPlay, autoPlayDelay]);
 
  return (
    <div
      ref={ref}
      className={cn(
        "relative group/cover block w-full px-6 py-3 transition duration-200 rounded-sm",
        hovered ? "bg-neutral-900" : "bg-transparent"
      )}
    >
      <AnimatePresence>
        {hovered && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{
              opacity: {
                duration: 0.2,
              },
            }}
            className="h-full w-full overflow-hidden absolute inset-0"
          >
            <motion.div
              animate={{
                translateX: ["-50%", "0%"],
              }}
              transition={{
                translateX: {
                  duration: 10,
                  ease: "linear",
                  repeat: Infinity,
                },
              }}
              className="w-[200%] h-full flex"
            >
              <SparklesCore
                background="transparent"
                minSize={0.4}
                maxSize={1}
                particleDensity={500}
                className="w-full h-full"
                particleColor="#FFFFFF"
              />
              <SparklesCore
                background="transparent"
                minSize={0.4}
                maxSize={1}
                particleDensity={500}
                className="w-full h-full"
                particleColor="#FFFFFF"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      {beamPositions.map((position, index) => (
        <Beam
          key={index}
          hovered={hovered}
          duration={Math.random() * 2 + 1}
          delay={Math.random() * 2 + 1}
          width={containerWidth}
          style={{
            top: `${position}px`,
          }}
        />
      ))}
      <motion.span
        key={`${animationPhase}-${String(hovered)}`}
        initial={{ opacity: animationPhase === "completed" ? 1 : 0 }} // Start visible if completed phase
        animate={{
          opacity: hovered || animationPhase === "completed" ? 1 : 0, // Show during animation or after completion
          scale: hovered ? 0.9 : animationPhase === "completed" ? 1.1 : 1, // Less scaling during animation, larger when completed
          x: hovered ? [0, -20, 20, -20, 20, 0] : 0, // Reduced movement for larger text
          y: hovered ? [0, 20, -20, 20, -20, 0] : 0, // Reduced movement for larger text
        }}
        exit={{
          opacity: animationPhase === "completed" ? 1 : 0, // Stay visible if completed
          filter: "none",
          scale: 1,
          x: 0,
          y: 0,
        }}
        transition={{
          opacity: {
            duration: animationPhase === "completed" ? 0.8 : 0.3, // Slower fade in for final state
          },
          duration: 0.2,
          x: {
            duration: 0.4, // Slower movement for larger text
            repeat: hovered ? Infinity : 0,
            repeatType: "loop",
          },
          y: {
            duration: 0.4, // Slower movement for larger text
            repeat: hovered ? Infinity : 0,
            repeatType: "loop",
          },
          scale: {
            duration: animationPhase === "completed" ? 0.8 : 0.2, // Slower scale for final state
          },
          filter: {
            duration: 0.2,
          },
        }}
        className={cn(
          "block w-full relative z-20 transition duration-500 font-bold text-center drop-shadow-lg",
          hovered 
            ? "text-white text-3xl tracking-widest" // White text with increased size and letter spacing during animation (matching the completed style)
            : animationPhase === "completed" 
              ? "text-white text-3xl tracking-widest" // White text with increased size and letter spacing when completed
              : "opacity-0 pointer-events-none", // Invisible initially
          className
        )}
      >
        {displayText}
      </motion.span>
      <CircleIcon className="absolute -right-[2px] -top-[2px]" hovered={hovered} />
      <CircleIcon className="absolute -bottom-[2px] -right-[2px]" delay={0.4} hovered={hovered} />
      <CircleIcon className="absolute -left-[2px] -top-[2px]" delay={0.8} hovered={hovered} />
      <CircleIcon className="absolute -bottom-[2px] -left-[2px]" delay={1.6} hovered={hovered} />
    </div>
  );
};
 
export const Beam = ({
  className,
  delay,
  duration,
  hovered,
  width = 600,
  ...svgProps
}) => {
  const id = useId();
 
  return (
    <motion.svg
      width={width ?? "600"}
      height="1"
      viewBox={`0 0 ${width ?? "600"} 1`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("absolute inset-x-0 w-full", className)}
      {...svgProps}
    >
      <motion.path
        d={`M0 0.5H${width ?? "600"}`}
        stroke={`url(#svgGradient-${id})`}
      />
 
      <defs>
        <motion.linearGradient
          id={`svgGradient-${id}`}
          key={String(hovered)}
          gradientUnits="userSpaceOnUse"
          initial={{
            x1: "0%",
            x2: hovered ? "-10%" : "-5%",
            y1: 0,
            y2: 0,
          }}
          animate={{
            x1: "110%",
            x2: hovered ? "100%" : "105%",
            y1: 0,
            y2: 0,
          }}
          transition={{
            duration: hovered ? 0.5 : duration ?? 2,
            ease: "linear",
            repeat: Infinity,
            delay: hovered ? Math.random() * (1 - 0.2) + 0.2 : 0,
            repeatDelay: hovered ? Math.random() * (2 - 1) + 1 : delay ?? 1,
          }}
        >
          <stop stopColor="#2EB9DF" stopOpacity="0" />
          <stop stopColor="#3b82f6" />
          <stop offset="1" stopColor="#3b82f6" stopOpacity="0" />
        </motion.linearGradient>
      </defs>
    </motion.svg>
  );
};
 
export const CircleIcon = ({
  className,
  delay,
  hovered
}) => {
  return (
    <div
      className={cn(
        `pointer-events-none animate-pulse h-2 w-2 rounded-full opacity-20`,
        hovered 
          ? "hidden bg-white" // When hovered or auto-play activated, hide circles and use white color
          : "group-hover/cover:hidden bg-neutral-600 dark:bg-white group-hover/cover:bg-white",
        className
      )}
    ></div>
  );
};

export default Cover;