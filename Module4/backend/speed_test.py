"""
Interactive Speed Test for Module 3 Analysis
Choose between Fast or Slow analysis at runtime.
"""

import asyncio
import json
import time
import os
from datetime import datetime
from Modules.SupportAgent.support_agent import LeftistCommonSupportAgent

def display_test_options():
    """Display test mode options to the user."""
    print("🔥 MODULE 3 SPEED TEST")
    print("=" * 50)
    print("Choose your test mode:")
    print()
    print("🐌 [1] SLOW MODE TEST (Maximum Accuracy)")
    print("   ⏱️  ALL 16 claims, 3 sources per claim, conservative delays")
    print("   🎯 Best accuracy and complete coverage")
    print()
    print("⚡ [2] FAST MODE TEST (Maximum Speed)")  
    print("   ⏱️  ~8 claims, 2 sources per claim, aggressive delays")
    print("   🚀 Maximum speed, fewer claims processed")
    print()
    print("🔄 [3] COMPARE BOTH MODES")
    print("   📊 Run both strategies and show comparison")
    print()
    print("❌ [4] EXIT")
    print()

def get_user_choice():
    """Get user's test mode choice."""
    while True:
        try:
            choice = input("👉 Enter your choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return 4
        except:
            print("❌ Invalid input. Please enter a number (1-4).")

def load_module3_claims():
    """Load claims from module3 JSON files."""
    leftist_path = "../../module3/backend/leftist.json"
    common_path = "../../module3/backend/common.json"
    
    leftist_claims = []
    common_claims = []
    
    try:
        # Load leftist claims
        if os.path.exists(leftist_path):
            with open(leftist_path, 'r', encoding='utf-8') as f:
                leftist_data = json.load(f)
                for claim in leftist_data:
                    leftist_claims.append({
                        "text": claim["text"],
                        "bias_x": claim["bias_x"],
                        "significance_y": claim["significance_y"],
                        "color": claim.get("color", "red"),
                        "type": "leftist"
                    })
            print(f"✅ Loaded {len(leftist_claims)} leftist claims from module3")
        else:
            print(f"⚠️  Leftist file not found: {leftist_path}")
            
        # Load common claims  
        if os.path.exists(common_path):
            with open(common_path, 'r', encoding='utf-8') as f:
                common_data = json.load(f)
                for claim in common_data:
                    common_claims.append({
                        "text": claim["text"],
                        "bias_x": claim["bias_x"], 
                        "significance_y": claim["significance_y"],
                        "color": claim.get("color", "green"),
                        "type": "common"
                    })
            print(f"✅ Loaded {len(common_claims)} common claims from module3")
        else:
            print(f"⚠️  Common file not found: {common_path}")
            
    except Exception as e:
        print(f"❌ Error loading claims: {e}")
        return [], []
    
    return leftist_claims, common_claims

async def run_speed_test_mode(mode_name, speed_mode):
    """Run speed test in the specified mode."""
    print(f"\n{'='*50}")
    print(f"🚀 {mode_name}")
    print("=" * 50)
    
    start_time = time.time()
    
    # Load real claims from module3
    print("📂 Loading claims from module3...")
    leftist_claims, common_claims = load_module3_claims()
    
    if not leftist_claims and not common_claims:
        print("❌ No claims loaded! Using sample data...")
        # Fallback to sample claims
        sample_claims = [
            {
                "text": "Climate change requires immediate government action",
                "bias_x": -2.5,
                "significance_y": 4.2,
                "type": "leftist"
            },
            {
                "text": "Universal healthcare is a fundamental right",
                "bias_x": -2.8, 
                "significance_y": 4.5,
                "type": "leftist"
            },
            {
                "text": "Economic policies should balance growth and environment",
                "bias_x": 0.0,
                "significance_y": 3.5,
                "type": "common"
            }
        ]
        all_claims = sample_claims
    else:
        # Select claims based on mode
        if speed_mode:
            # Fast mode: Use fewer claims for speed (5 leftist + 3 common = 8 claims)
            selected_leftist = leftist_claims[:5] if len(leftist_claims) >= 5 else leftist_claims
            selected_common = common_claims[:3] if len(common_claims) >= 3 else common_claims
            all_claims = selected_leftist + selected_common
        else:
            # Slow mode: Use ALL claims for maximum accuracy
            all_claims = leftist_claims + common_claims
    
    print(f"📊 Testing with {len(all_claims)} claims")
    if leftist_claims or common_claims:
        print(f"   🔴 Leftist: {len([c for c in all_claims if c['type'] == 'leftist'])}")
        print(f"   🟢 Common: {len([c for c in all_claims if c['type'] == 'common'])}")
    
    if speed_mode:
        print("⚡ SPEED MODE: 2 sources per claim, faster delays, FEWER claims")
        total_available = len(leftist_claims) + len(common_claims)
        print(f"   📊 Processing {len(all_claims)}/{total_available} claims for speed")
    else:
        print("🎯 ACCURACY MODE: 3 sources per claim, conservative delays, ALL claims")
        print(f"   📊 Processing ALL {len(all_claims)} claims for maximum accuracy")
    print()
    
    # Initialize agent with selected mode
    agent = LeftistCommonSupportAgent(speed_mode=speed_mode)
    
    results = {
        "total_time": 0,
        "successful_claims": 0,
        "total_sources": 0,
        "errors": []
    }
    
    for i, claim in enumerate(all_claims, 1):
        print(f"🔄 Processing {claim['type']} claim {i}/{len(all_claims)}")
        print(f"   📝 Claim: {claim['text'][:60]}...")
        
        claim_start = time.time()
        
        try:
            # Search for supporting content
            search_start = time.time()
            sources = await agent.search_supporting_content(claim)
            search_time = time.time() - search_start
            
            # Extract content from first source for demo
            if sources:
                extract_start = time.time()
                content = await agent.extract_and_store_content(sources[:1], claim)
                extract_time = time.time() - extract_start
            else:
                extract_time = 0
                content = []
            
            claim_time = time.time() - claim_start
            
            results["successful_claims"] += 1
            results["total_sources"] += len(sources)
            
            print(f"   ✅ Success: {len(sources)} sources in {claim_time:.1f}s")
            print(f"      🔍 Search: {search_time:.1f}s, 📥 Extract: {extract_time:.1f}s")
            
        except Exception as e:
            results["errors"].append(f"Claim {i}: {str(e)}")
            print(f"   ❌ Error: {e}")
    
    total_time = time.time() - start_time
    results["total_time"] = total_time
    
    # Calculate statistics
    avg_time = total_time / len(all_claims) if all_claims else 0
    success_rate = (results["successful_claims"] / len(all_claims) * 100) if all_claims else 0
    
    # Check if we tested all claims or just a subset
    total_available_claims = len(leftist_claims) + len(common_claims)
    tested_all_claims = len(all_claims) == total_available_claims
    
    # Add detailed metrics to results
    results.update({
        "average_time_per_claim": avg_time,
        "success_rate_percent": success_rate,
        "total_claims_processed": len(all_claims),
        "total_available_claims": total_available_claims,
        "tested_all_claims": tested_all_claims,
        "leftist_claims_available": len(leftist_claims),
        "common_claims_available": len(common_claims),
        "leftist_claims_processed": len([c for c in all_claims if c['type'] == 'leftist']),
        "common_claims_processed": len([c for c in all_claims if c['type'] == 'common']),
        "mode_name": mode_name,
        "speed_mode": speed_mode,
        "total_time_minutes": total_time / 60
    })
    
    if not tested_all_claims:
        estimated_full_time = avg_time * total_available_claims / 60
        results["estimated_full_time_minutes"] = estimated_full_time
    
    print(f"🎯 {mode_name} RESULTS")
    print("=" * 50)
    print(f"⏱️  Total Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"📊 Average per claim: {avg_time:.1f}s") 
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print(f"🔍 Total Sources Found: {results['total_sources']}")
    
    if tested_all_claims:
        print(f"✅ FULL MODULE TIME: {total_time/60:.1f} minutes")
        print(f"   📊 Processed ALL {len(all_claims)} claims from module3")
    else:
        estimated_full_time = avg_time * total_available_claims / 60
        print(f"🎯 Estimated Full Module Time: {estimated_full_time:.1f} minutes")
        print(f"   📊 Based on {len(all_claims)}/{total_available_claims} claims tested")
    
    if results["errors"]:
        print(f"⚠️  Errors: {len(results['errors'])}")
        for error in results["errors"][:3]:  # Show first 3 errors
            print(f"   - {error}")
        if len(results["errors"]) > 3:
            print(f"   ... and {len(results['errors']) - 3} more errors")
    
    if speed_mode:
        print("⚠️  SPEED MODE: Results may be less comprehensive")
    else:
        print("🎯 ACCURACY MODE: Maximum reliability and coverage")
    
    return results

async def interactive_speed_test():
    """Main interactive speed test function."""
    while True:
        display_test_options()
        choice = get_user_choice()
        
        if choice == 4:  # Exit
            print("👋 Thank you for using the speed test!")
            break
            
        elif choice == 1:  # Slow Mode
            print("\n🐌 You selected: SLOW MODE TEST")
            confirm = input("Run slow mode test? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                await run_speed_test_mode("🐌 SLOW MODE TEST", False)
                
        elif choice == 2:  # Fast Mode
            print("\n⚡ You selected: FAST MODE TEST")
            print("⚠️  Warning: Speed mode may be less accurate")
            confirm = input("Run fast mode test? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                await run_speed_test_mode("⚡ FAST MODE TEST", True)
                
        elif choice == 3:  # Both Modes
            print("\n🔄 You selected: COMPARE BOTH MODES")
            confirm = input("Run comparison test? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                
                # Run slow mode
                slow_results = await run_speed_test_mode("🐌 SLOW MODE TEST", False)
                
                print("\n" + "="*50)
                print("🔄 Switching to Fast Mode...")
                await asyncio.sleep(2)
                
                # Run fast mode  
                fast_results = await run_speed_test_mode("⚡ FAST MODE TEST", True)
                
                # Compare results
                print(f"\n{'='*50}")
                print("📊 COMPARISON RESULTS")
                print("="*50)
                
                time_diff = slow_results['total_time'] - fast_results['total_time']
                speed_improvement = (time_diff / slow_results['total_time']) * 100
                
                print(f"⏱️  TIME COMPARISON:")
                print(f"   🐌 Slow Mode: {slow_results['total_time']:.1f}s")
                print(f"   ⚡ Fast Mode: {fast_results['total_time']:.1f}s")
                print(f"   💨 Time Saved: {time_diff:.1f}s ({speed_improvement:.1f}% faster)")
                
                print(f"\n🔍 SOURCE COMPARISON:")
                print(f"   🐌 Slow Mode: {slow_results['total_sources']} sources")
                print(f"   ⚡ Fast Mode: {fast_results['total_sources']} sources")
                
                print(f"\n💡 RECOMMENDATION:")
                if speed_improvement > 20:
                    print(f"   ⚡ Fast mode offers {speed_improvement:.0f}% speed improvement")
                    print(f"   💡 Good for exploration and quick results")
                print(f"   🎯 Slow mode provides maximum accuracy and coverage")
        
        # Ask to continue
        print(f"\n{'='*50}")
        another = input("🔄 Run another test? (y/n): ").strip().lower()
        if another not in ['y', 'yes']:
            print("👋 Thanks for testing!")
            break

if __name__ == "__main__":
    asyncio.run(interactive_speed_test())