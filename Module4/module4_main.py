#!/usr/bin/env python3
"""
Module 4 - Political Perspective Analysis Agents
Main entry point for leftist and rightist content analysis
"""

import asyncio
import sys
import os
from datetime import datetime

def print_module4_banner():
    """Print Module 4 banner and information."""
    print("="*70)
    print("🎯 MODULE 4 - POLITICAL PERSPECTIVE ANALYSIS AGENTS")
    print("="*70)
    print("📊 Intelligent content analysis for political perspectives")
    print("🔴 Leftist Agent: Analyzes leftist + common claims")
    print("🔵 Rightist Agent: Analyzes rightist + common claims")
    print("⚡ Smart Selection: Bias-diverse sampling for representative results")
    print("📄 Full Extraction: Complete web content with structured JSON output")
    print("="*70)

def show_agent_menu():
    """Display agent selection menu."""
    print("\n🎯 SELECT ANALYSIS AGENT:")
    print("1. 🔴 LEFTIST AGENT - Analyze leftist + common claims")
    print("2. 🔵 RIGHTIST AGENT - Analyze rightist + common claims")
    print("3. 🔄 RUN BOTH AGENTS - Comparative analysis")
    print("4. ℹ️  SHOW MODULE INFO")
    print("5. ❌ EXIT")
    print()

def show_module_info():
    """Display detailed module information."""
    print("\n📋 MODULE 4 INFORMATION")
    print("="*50)
    print("🎯 Purpose: Political perspective content analysis")
    print("📂 Data Sources:")
    print("   - leftist.json (leftist claims)")
    print("   - rightist.json (rightist claims)") 
    print("   - common.json (neutral claims)")
    print("\n⚙️ Analysis Modes:")
    print("   - Fast Mode: ~8 diverse claims, 2-3 minutes")
    print("   - Slow Mode: All claims, 4-6 minutes")
    print("   - Both Modes: Comparative analysis")
    print("\n📊 Output:")
    print("   - JSON files with extracted content")
    print("   - Performance metrics and timing")
    print("   - Source URLs and success rates")
    print("\n🔧 Configuration:")
    print("   - Bias-diverse claim selection")
    print("   - Intelligent web scraping")
    print("   - Vector database content storage")

async def run_leftist_agent():
    """Run the leftist analysis agent."""
    try:
        # Import and run leftist agent
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        from leftistagent import test_with_content
        
        print("\n🔴 STARTING LEFTIST AGENT...")
        print("="*50)
        await test_with_content()
        
    except ImportError as e:
        print(f"❌ Error importing leftist agent: {e}")
        print("💡 Make sure leftistagent.py exists in the backend directory")
    except Exception as e:
        print(f"❌ Error running leftist agent: {e}")

async def run_rightist_agent():
    """Run the rightist analysis agent."""
    try:
        # Import and run rightist agent
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        from rightistagent import test_with_content
        
        print("\n🔵 STARTING RIGHTIST AGENT...")
        print("="*50)
        await test_with_content()
        
    except ImportError as e:
        print(f"❌ Error importing rightist agent: {e}")
        print("💡 Make sure rightistagent.py exists in the backend directory")
    except Exception as e:
        print(f"❌ Error running rightist agent: {e}")

async def run_both_agents():
    """Run both agents for comparative analysis."""
    print("\n🔄 RUNNING COMPARATIVE ANALYSIS")
    print("="*50)
    print("This will run both leftist and rightist agents sequentially")
    
    confirm = input("Continue with both agents? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Cancelled")
        return
    
    start_time = datetime.now()
    
    # Run leftist agent
    print(f"\n{'='*50}")
    print("🔴 PHASE 1: LEFTIST AGENT ANALYSIS")
    print("="*50)
    await run_leftist_agent()
    
    # Run rightist agent
    print(f"\n{'='*50}")
    print("🔵 PHASE 2: RIGHTIST AGENT ANALYSIS")
    print("="*50)
    await run_rightist_agent()
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*50}")
    print("✅ COMPARATIVE ANALYSIS COMPLETED")
    print("="*50)
    print(f"⏱️  Total Duration: {duration}")
    print(f"📁 Check backend directory for JSON output files:")
    print(f"   - enhanced_content_test_*.json (leftist results)")
    print(f"   - rightist_content_test_*.json (rightist results)")
    print("="*50)

async def main():
    """Main module entry point."""
    print_module4_banner()
    
    while True:
        show_agent_menu()
        
        try:
            choice = input("👉 Enter your choice (1-5): ").strip()
            
            if choice == "1":
                await run_leftist_agent()
                
            elif choice == "2":
                await run_rightist_agent()
                
            elif choice == "3":
                await run_both_agents()
                
            elif choice == "4":
                show_module_info()
                
            elif choice == "5":
                print("\n👋 Exiting Module 4...")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Ask to continue
        print("\n" + "="*50)
        continue_choice = input("🔄 Return to main menu? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            print("👋 Goodbye!")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Module 4 terminated by user")
    except Exception as e:
        print(f"❌ Module 4 error: {e}")