"""
Rightist Agent - Enhanced test with extracted content in JSON output
"""

import asyncio
import json
import time
from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Modules.SupportAgent.support_agent import LeftistCommonSupportAgent

async def research_with_perspectives(perspectives_data, analysis_mode="fast"):
    """
    Run deep research analysis using perspectives from Module3.
    
    Args:
        perspectives_data: Dict containing rightist and common perspectives
        analysis_mode: "fast" or "slow" mode
        
    Returns:
        Dict with research results and extracted content
    """
    print(f"\n🔵 RIGHTIST AGENT - DEEP RESEARCH ({analysis_mode.upper()} MODE)")
    print("=" * 60)
    
    start_time = time.time()
    speed_mode = analysis_mode == "fast"
    
    # Extract claims from perspectives data
    rightist_claims = perspectives_data.get('rightist', [])
    common_claims = perspectives_data.get('common', [])
    
    # Prepare claims for analysis
    all_claims = []
    for claim_data in rightist_claims:
        if isinstance(claim_data, dict) and 'text' in claim_data:
            all_claims.append({
                "text": claim_data['text'],
                "bias_x": claim_data.get('bias_x', 0),
                "significance_y": claim_data.get('significance_y', 0),
                "color": claim_data.get('color', 'unknown'),
                "type": "rightist"
            })
    
    for claim_data in common_claims:
        if isinstance(claim_data, dict) and 'text' in claim_data:
            all_claims.append({
                "text": claim_data['text'],
                "bias_x": claim_data.get('bias_x', 0),
                "significance_y": claim_data.get('significance_y', 0),
                "color": claim_data.get('color', 'unknown'),
                "type": "common"
            })
    
    if not all_claims:
        return {
            "error": "No valid claims found in perspectives data",
            "total_time": 0,
            "claims_processed": 0
        }
    
    # Select claims based on mode
    if speed_mode:
        # Fast mode: Select diverse subset
        selected_rightist = select_diverse_claims([c for c in all_claims if c['type'] == 'rightist'], 3)
        selected_common = select_diverse_claims([c for c in all_claims if c['type'] == 'common'], 2)
        claims_to_process = selected_rightist + selected_common
    else:
        # Slow mode: Process all claims
        claims_to_process = all_claims
    
    print(f"📊 Processing {len(claims_to_process)}/{len(all_claims)} claims")
    print(f"   🔵 Rightist: {len([c for c in claims_to_process if c['type'] == 'rightist'])}")
    print(f"   🟢 Common: {len([c for c in claims_to_process if c['type'] == 'common'])}")
    
    # Initialize rightist agent with separate database
    agent = LeftistCommonSupportAgent(
        speed_mode=speed_mode, 
        collection_name="rightist_evidence", 
        db_name="rightist_evidence_db"
    )
    
    results = {
        "agent_type": "rightist",
        "analysis_mode": analysis_mode,
        "total_time": 0,
        "successful_claims": 0,
        "total_sources": 0,
        "errors": [],
        "claims_with_content": [],
        "total_claims_available": len(all_claims),
        "claims_processed": len(claims_to_process)
    }
    
    # Process each claim
    for i, claim in enumerate(claims_to_process, 1):
        print(f"🔄 Processing {claim['type']} claim {i}/{len(claims_to_process)}")
        print(f"   📝 Claim: {claim['text'][:60]}...")
        
        claim_start = time.time()
        claim_data = {
            "claim_number": i,
            "claim_text": claim['text'],
            "claim_type": claim['type'],
            "bias_x": claim.get('bias_x', 0),
            "significance_y": claim.get('significance_y', 0),
            "sources_found": [],
            "extracted_content": [],
            "processing_time_seconds": 0,
            "success": False
        }
        
        try:
            # Search for supporting content
            sources = await agent.search_supporting_content(claim)
            claim_data["sources_found"] = sources
            
            # Extract content from sources
            if sources:
                content = await agent.extract_and_store_content(sources, claim)
                
                if content:
                    for idx, content_item in enumerate(content):
                        if hasattr(content_item, '__dict__'):
                            content_dict = content_item.__dict__
                        elif isinstance(content_item, dict):
                            content_dict = content_item
                        else:
                            content_dict = {
                                "content": str(content_item),
                                "source_index": idx
                            }
                        claim_data["extracted_content"].append(content_dict)
            
            claim_time = time.time() - claim_start
            claim_data["processing_time_seconds"] = claim_time
            claim_data["success"] = True
            
            results["successful_claims"] += 1
            results["total_sources"] += len(sources)
            
            print(f"   ✅ Success: {len(sources)} sources, {len(claim_data['extracted_content'])} content pieces")
            
        except Exception as e:
            claim_time = time.time() - claim_start
            claim_data["processing_time_seconds"] = claim_time
            claim_data["error"] = str(e)
            results["errors"].append(f"Claim {i}: {str(e)}")
            print(f"   ❌ Error: {e}")
        
        results["claims_with_content"].append(claim_data)
    
    total_time = time.time() - start_time
    results["total_time"] = total_time
    results["average_time_per_claim"] = total_time / len(claims_to_process) if claims_to_process else 0
    results["success_rate_percent"] = (results["successful_claims"] / len(claims_to_process) * 100) if claims_to_process else 0
    
    print(f"\n🎯 RIGHTIST RESEARCH COMPLETED")
    print(f"⏱️  Total Time: {total_time:.1f}s")
    print(f"📈 Success Rate: {results['success_rate_percent']:.1f}%")
    print(f"🔍 Total Sources: {results['total_sources']}")
    print(f"📄 Content Pieces: {sum(len(c['extracted_content']) for c in results['claims_with_content'])}")
    
    return results

def select_diverse_claims(claims, target_count):
    """Select claims with diverse bias values/colors for representative sampling."""
    if len(claims) <= target_count:
        return claims
    
    # Group claims by color for diversity
    color_groups = {}
    for claim in claims:
        color = claim.get('color', 'unknown')
        if color not in color_groups:
            color_groups[color] = []
        color_groups[color].append(claim)
    
    selected = []
    colors = list(color_groups.keys())
    
    # Distribute selection across colors proportionally
    while len(selected) < target_count and colors:
        for color in colors[:]:
            if len(selected) >= target_count:
                break
            if color_groups[color]:
                selected.append(color_groups[color].pop(0))
            else:
                colors.remove(color)
    
    return selected

def print_color_distribution(claims, claim_type):
    """Print color distribution of selected claims."""
    if not claims:
        return
    
    color_count = {}
    for claim in claims:
        color = claim.get('color', 'unknown')
        color_count[color] = color_count.get(color, 0) + 1
    
    color_summary = ', '.join([f"{count} {color}" for color, count in color_count.items()])
    print(f"   📊 {claim_type.title()}: {color_summary}")

def load_module3_rightist_claims():
    """Load rightist and common claims from module3 JSON files."""
    rightist_claims = []
    common_claims = []
    
    # Path to module3 backend directory
    module3_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "module3", "backend")
    
    try:
        # Load rightist claims
        rightist_file = os.path.join(module3_path, "rightist.json")
        if os.path.exists(rightist_file):
            with open(rightist_file, 'r', encoding='utf-8') as f:
                rightist_data = json.load(f)
                for item in rightist_data:
                    rightist_claims.append({
                        "text": item["text"],
                        "bias_x": item.get("bias_x", 0),
                        "significance_y": item.get("significance_y", 0),
                        "color": item.get("color", "unknown"),
                        "type": "rightist"
                    })
            print(f"✅ Loaded {len(rightist_claims)} rightist claims from module3")
        else:
            print(f"❌ Rightist file not found: {rightist_file}")
            
        # Load common claims
        common_file = os.path.join(module3_path, "common.json")
        if os.path.exists(common_file):
            with open(common_file, 'r', encoding='utf-8') as f:
                common_data = json.load(f)
                for item in common_data:
                    common_claims.append({
                        "text": item["text"],
                        "bias_x": item.get("bias_x", 0),
                        "significance_y": item.get("significance_y", 0),
                        "color": item.get("color", "unknown"),
                        "type": "common"
                    })
            print(f"✅ Loaded {len(common_claims)} common claims from module3")
        else:
            print(f"❌ Common file not found: {common_file}")
            
    except Exception as e:
        print(f"❌ Error loading claims: {e}")
    
    return rightist_claims, common_claims

async def run_enhanced_test_mode(mode_name, speed_mode):
    """Run test with extracted content capture."""
    print(f"\n{'='*50}")
    print(f"🚀 {mode_name}")
    print("=" * 50)
    
    start_time = time.time()
    
    # Load real claims from module3
    print("📂 Loading claims from module3...")
    rightist_claims, common_claims = load_module3_rightist_claims()
    
    if not rightist_claims and not common_claims:
        print("❌ No claims loaded!")
        return None
    
    # Select claims based on mode
    if speed_mode:
        # Fast mode: Use diverse selection based on bias/color distribution
        selected_rightist = select_diverse_claims(rightist_claims, 5)
        selected_common = select_diverse_claims(common_claims, 3)
        all_claims = selected_rightist + selected_common
        print(f"⚡ Fast mode selection:")
        print_color_distribution(selected_rightist, "rightist")
        print_color_distribution(selected_common, "common")
    else:
        # Slow mode: Use ALL claims for maximum accuracy
        all_claims = rightist_claims + common_claims
    
    print(f"📊 Testing with {len(all_claims)} claims")
    print(f"   🔵 Rightist: {len([c for c in all_claims if c['type'] == 'rightist'])}")
    print(f"   🟢 Common: {len([c for c in all_claims if c['type'] == 'common'])}")
    
    if speed_mode:
        print("⚡ SPEED MODE: 2 sources per claim, faster delays, FEWER claims")
        total_available = len(rightist_claims) + len(common_claims)
        print(f"   📊 Processing {len(all_claims)}/{total_available} claims for speed")
    else:
        print("🎯 ACCURACY MODE: 3 sources per claim, conservative delays, ALL claims")
        print(f"   📊 Processing ALL {len(all_claims)} claims for maximum accuracy")
    print()
    
    # Initialize rightist agent with separate database
    agent = LeftistCommonSupportAgent(
        speed_mode=speed_mode, 
        collection_name="rightist_evidence", 
        db_name="rightist_evidence_db"
    )
    
    results = {
        "total_time": 0,
        "successful_claims": 0,
        "total_sources": 0,
        "errors": [],
        "claims_with_content": []  # Store claims with their extracted content
    }
    
    for i, claim in enumerate(all_claims, 1):
        print(f"🔄 Processing {claim['type']} claim {i}/{len(all_claims)}")
        print(f"   📝 Claim: {claim['text'][:60]}...")
        
        claim_start = time.time()
        claim_data = {
            "claim_number": i,
            "claim_text": claim['text'],
            "claim_type": claim['type'],
            "bias_x": claim.get('bias_x', 0),
            "significance_y": claim.get('significance_y', 0),
            "sources_found": [],
            "extracted_content": [],
            "processing_time_seconds": 0,
            "search_time_seconds": 0,
            "extract_time_seconds": 0,
            "success": False
        }
        
        try:
            # Search for supporting content
            search_start = time.time()
            sources = await agent.search_supporting_content(claim)
            search_time = time.time() - search_start
            claim_data["search_time_seconds"] = search_time
            claim_data["sources_found"] = sources
            
            # Extract content from sources
            if sources:
                extract_start = time.time()
                content = await agent.extract_and_store_content(sources, claim)
                extract_time = time.time() - extract_start
                claim_data["extract_time_seconds"] = extract_time
                
                # Store the extracted content details
                if content:
                    for idx, content_item in enumerate(content):
                        if hasattr(content_item, '__dict__'):
                            # If it's an object, convert to dict
                            content_dict = content_item.__dict__
                        elif isinstance(content_item, dict):
                            content_dict = content_item
                        else:
                            # If it's just text
                            content_dict = {
                                "content": str(content_item),
                                "source_index": idx
                            }
                        
                        claim_data["extracted_content"].append(content_dict)
            else:
                extract_time = 0
                claim_data["extract_time_seconds"] = 0
            
            claim_time = time.time() - claim_start
            claim_data["processing_time_seconds"] = claim_time
            claim_data["success"] = True
            
            results["successful_claims"] += 1
            results["total_sources"] += len(sources)
            
            print(f"   ✅ Success: {len(sources)} sources in {claim_time:.1f}s")
            print(f"      🔍 Search: {search_time:.1f}s, 📥 Extract: {extract_time:.1f}s")
            print(f"      📄 Content pieces: {len(claim_data['extracted_content'])}")
            
        except Exception as e:
            claim_time = time.time() - claim_start
            claim_data["processing_time_seconds"] = claim_time
            claim_data["error"] = str(e)
            results["errors"].append(f"Claim {i}: {str(e)}")
            print(f"   ❌ Error: {e}")
        
        # Add claim data to results
        results["claims_with_content"].append(claim_data)
    
    total_time = time.time() - start_time
    results["total_time"] = total_time
    
    # Calculate statistics
    avg_time = total_time / len(all_claims) if all_claims else 0
    success_rate = (results["successful_claims"] / len(all_claims) * 100) if all_claims else 0
    
    # Check if we tested all claims or just a subset
    total_available_claims = len(rightist_claims) + len(common_claims)
    tested_all_claims = len(all_claims) == total_available_claims
    
    # Add detailed metrics to results
    results.update({
        "average_time_per_claim": avg_time,
        "success_rate_percent": success_rate,
        "total_claims_processed": len(all_claims),
        "total_available_claims": total_available_claims,
        "tested_all_claims": tested_all_claims,
        "rightist_claims_available": len(rightist_claims),
        "common_claims_available": len(common_claims),
        "rightist_claims_processed": len([c for c in all_claims if c['type'] == 'rightist']),
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
    print(f"📄 Claims with Content: {len([c for c in results['claims_with_content'] if c['success']])}")
    
    if tested_all_claims:
        print(f"✅ FULL MODULE TIME: {total_time/60:.1f} minutes")
        print(f"   📊 Processed ALL {len(all_claims)} claims from module3")
    else:
        estimated_full_time = avg_time * total_available_claims / 60
        print(f"🎯 Estimated Full Module Time: {estimated_full_time:.1f} minutes")
        print(f"   📊 Based on {len(all_claims)}/{total_available_claims} claims tested")
    
    if results["errors"]:
        print(f"⚠️  Errors: {len(results['errors'])}")
    
    if speed_mode:
        print("⚠️  SPEED MODE: Results may be less comprehensive")
    else:
        print("🎯 ACCURACY MODE: Maximum reliability and coverage")
    
    return results

async def test_with_content():
    """Test with extracted content included in JSON."""
    print("🧪 RIGHTIST AGENT - ENHANCED TEST WITH EXTRACTED CONTENT")
    print("=" * 60)
    print("Choose test mode:")
    print("1. 🐌 SLOW MODE (ALL rightist + common claims, maximum accuracy)")
    print("2. ⚡ FAST MODE (~8 claims, maximum speed)")
    print("3. 🔄 BOTH MODES (Comparison)")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("❌ Input error or interruption")
        return
    
    test_start_time = time.time()
    test_results = {
        "test_session": {
            "timestamp": datetime.now().isoformat(),
            "test_type": "rightist_content_test",
            "agent_type": "rightist",
            "version": "2.0",
            "choice_selected": choice,
            "includes_extracted_content": True
        },
        "results": []
    }
    
    if choice == "1":
        print("\n🐌 Running SLOW MODE with extracted content...")
        slow_results = await run_enhanced_test_mode("🐌 RIGHTIST SLOW MODE - WITH CONTENT", False)
        if slow_results:
            test_results["results"].append({
                "mode": "slow",
                "description": "All rightist + common claims with extracted content",
                "speed_mode": False,
                "data": slow_results
            })
        
    elif choice == "2":
        print("\n⚡ Running FAST MODE with extracted content...")
        fast_results = await run_enhanced_test_mode("⚡ RIGHTIST FAST MODE - WITH CONTENT", True)
        if fast_results:
            test_results["results"].append({
                "mode": "fast",
                "description": "Subset rightist + common claims with extracted content",
                "speed_mode": True,
                "data": fast_results
            })
        
    elif choice == "3":
        print("\n🔄 Running BOTH MODES with extracted content...")
        
        print("\n🐌 Testing SLOW MODE...")
        slow_results = await run_enhanced_test_mode("🐌 RIGHTIST SLOW MODE - WITH CONTENT", False)
        
        print("\n⚡ Testing FAST MODE...")
        fast_results = await run_enhanced_test_mode("⚡ RIGHTIST FAST MODE - WITH CONTENT", True)
        
        if slow_results:
            test_results["results"].append({
                "mode": "slow",
                "description": "All rightist + common claims with extracted content",
                "speed_mode": False,
                "data": slow_results
            })
        
        if fast_results:
            test_results["results"].append({
                "mode": "fast",
                "description": "Subset rightist + common claims with extracted content",
                "speed_mode": True,
                "data": fast_results
            })
        
        # Add comparison if both successful
        if slow_results and fast_results:
            time_diff = slow_results['total_time'] - fast_results['total_time']
            speed_improvement = (time_diff / slow_results['total_time']) * 100
            
            test_results["comparison"] = {
                "time_difference_seconds": time_diff,
                "speed_improvement_percent": speed_improvement,
                "slow_mode_minutes": slow_results['total_time'] / 60,
                "fast_mode_minutes": fast_results['total_time'] / 60,
                "slow_mode_content_pieces": sum(len(c['extracted_content']) for c in slow_results['claims_with_content']),
                "fast_mode_content_pieces": sum(len(c['extracted_content']) for c in fast_results['claims_with_content'])
            }
            
            print(f"\n📊 CONTENT COMPARISON:")
            print(f"🐌 Slow Mode: {test_results['comparison']['slow_mode_content_pieces']} content pieces")
            print(f"⚡ Fast Mode: {test_results['comparison']['fast_mode_content_pieces']} content pieces")
        
    else:
        print("❌ Invalid choice!")
        return
    
    # Add total test duration
    total_test_time = time.time() - test_start_time
    test_results["test_session"]["total_duration_seconds"] = total_test_time
    test_results["test_session"]["total_duration_minutes"] = total_test_time / 60
    
    # Save to JSON with enhanced filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rightist_content_test_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("✅ RIGHTIST AGENT TEST COMPLETED!")
    print(f"📊 Total duration: {total_test_time/60:.1f} minutes")
    print(f"📁 Results with extracted content saved to: {filename}")
    
    # Show content summary
    total_content_pieces = 0
    for result in test_results["results"]:
        content_pieces = sum(len(c['extracted_content']) for c in result['data']['claims_with_content'])
        total_content_pieces += content_pieces
        print(f"   📄 {result['mode'].title()} Mode: {content_pieces} content pieces extracted")
    
    print(f"📋 Total extracted content pieces: {total_content_pieces}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_with_content())