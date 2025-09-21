import subprocess, json, time, threading, asyncio, importlib.util, sys, os, uuid, logging
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import google.generativeai as genai
#hello ive added this as a test
#yes ok  =D
#lol
app = FastAPI(title="Pipeline Orchestrator (Module1, Module2, Module3 & Module4)", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = Path(__file__).resolve().parent
MOD1_DIR = BASE / "Module1" / "backend"  # Module1 path
MOD2_DIR = BASE / "Module2" / "backend"  # Module2 path
MOD3_DIR = BASE / "module3" / "backend"  # Module3 path (Cache path)
MOD4_DIR = BASE / "Module4" / "backend"  # Module4 path
PYTHON_EXE = "python"  # Use system python instead of venv

STATE = {
    "stage": "idle",
    "progress": 0,
    "error": None,
    "started_at": None,
    "ended_at": None
}

LOCK = threading.Lock()

# Store active WebSocket connections
active_websockets = set()

# Module4 WebSocket connections for real-time streaming
module4_websockets = set()

# Debate WebSocket connections for real-time debate streaming
debate_websockets = set()

# Perspective data storage for reconnecting clients
perspective_cache = {}

# Module4 job tracking
module4_jobs = {}

# ==================== DEBATE AGENT ====================

class DebateAgent:
    """Facilitates structured debates between political perspective agents."""
    
    def __init__(self):
        """Initialize the debate agent."""
        self.gemini_key = os.getenv("GENAI_API_KEY") or "AIzaSyBvrogpxh3gVk7hkvzSgr_PBE_wzJ1DfSQ"
        
        # Initialize Gemini AI for debate moderation
        genai.configure(api_key=self.gemini_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Debate configuration
        self.max_rounds = 5
        self.points_to_win = 3
        self.timeout_penalty = 1  # Points awarded for non-response
        
        # Scoring system
        self.scoring_criteria = {
            "evidence_quality": 2,      # Strong factual evidence
            "source_credibility": 2,    # Reliable, authoritative sources  
            "logical_consistency": 1,   # Internal logic and coherence
            "response_relevance": 1,    # Directly addresses opponent's points
            "factual_accuracy": 2,      # Verifiable facts vs speculation
            "no_response_penalty": 1    # Awarded when opponent can't respond
        }
        
        print("Debate Agent initialized")
    
    async def conduct_debate(self, leftist_results: Dict, rightist_results: Dict) -> Dict:
        """
        Conduct a structured debate between leftist and rightist research results.
        
        Args:
            leftist_results: Research results from leftist agent
            rightist_results: Research results from rightist agent
            
        Returns:
            Dict containing debate results, scores, and winner determination
        """
        print("🎯 Starting structured debate between agents")
        
        debate_session = {
            "start_time": time.time(),
            "rounds": [],
            "scores": {"leftist": 0, "rightist": 0},
            "winner": None,
            "total_rounds": 0,
            "debate_summary": "",
            "key_arguments": {"leftist": [], "rightist": []},
            "evidence_analysis": {}
        }
        
        # Extract key claims and evidence for debate
        leftist_claims = self._extract_debate_points(leftist_results, "leftist")
        rightist_claims = self._extract_debate_points(rightist_results, "rightist")
        
        print(f"   📊 Leftist claims: {len(leftist_claims)}")
        print(f"   📊 Rightist claims: {len(rightist_claims)}")
        
        # Conduct debate rounds
        for round_num in range(1, self.max_rounds + 1):
            print(f"\n🔥 DEBATE ROUND {round_num}")
            print("=" * 50)
            
            # Determine who goes first (alternating)
            if round_num % 2 == 1:
                first_agent = "leftist"
                second_agent = "rightist"
                first_claims = leftist_claims
                second_claims = rightist_claims
            else:
                first_agent = "rightist"
                second_agent = "leftist"
                first_claims = rightist_claims
                second_claims = leftist_claims
            
            # Conduct round
            round_result = await self._conduct_round(
                round_num, first_agent, second_agent, 
                first_claims, second_claims, debate_session["rounds"]
            )
            
            debate_session["rounds"].append(round_result)
            debate_session["total_rounds"] = round_num
            
            # Update scores
            # Update scores - there's always a winner now
            debate_session["scores"][round_result["round_winner"]] += round_result["points_awarded"]
            
            print(f"   🏆 Round {round_num} winner: {round_result['round_winner'].upper()} (Better Information)")
            print(f"   📈 Current scores - Leftist: {debate_session['scores']['leftist']}, Rightist: {debate_session['scores']['rightist']}")
            
            # Check for early victory
            if (debate_session["scores"]["leftist"] >= self.points_to_win or 
                debate_session["scores"]["rightist"] >= self.points_to_win):
                print(f"\n🎯 Early victory achieved after {round_num} rounds!")
                break
            
            # Brief pause between rounds
            await asyncio.sleep(1)
        
        # Determine final winner
        debate_session["winner"] = self._determine_final_winner(debate_session["scores"])
        debate_session["duration"] = time.time() - debate_session["start_time"]
        
        # Generate debate summary
        debate_session["debate_summary"] = await self._generate_debate_summary(debate_session)
        
        print(f"\n🏁 DEBATE CONCLUDED")
        print(f"   ⏱️  Duration: {debate_session['duration']:.1f}s")
        print(f"   🏆 Winner: {debate_session['winner'].upper()} (Most Accurate Information)")
        print(f"   📊 Final scores - Leftist: {debate_session['scores']['leftist']}, Rightist: {debate_session['scores']['rightist']}")
        
        return debate_session
    
    def _extract_debate_points(self, research_results: Dict, agent_type: str) -> List[Dict]:
        """Extract key debate points from research results."""
        debate_points = []
        
        if research_results and "claims_with_content" in research_results:
            for claim in research_results["claims_with_content"]:
                if claim.get("success") and claim.get("extracted_content"):
                    
                    # Extract evidence and sources
                    evidence = []
                    sources = []
                    
                    for content_item in claim["extracted_content"]:
                        if content_item.get("content"):
                            evidence.append(content_item["content"])
                        if content_item.get("url"):
                            sources.append(content_item["url"])
                    
                    if evidence:  # Only include claims with actual evidence
                        debate_points.append({
                            "claim": claim.get("claim", ""),
                            "evidence": evidence[:3],  # Top 3 pieces of evidence
                            "sources": sources[:3],    # Top 3 sources
                            "agent_type": agent_type,
                            "strength": len(evidence)  # More evidence = stronger point
                        })
        
        # Sort by evidence strength (more evidence = stronger argument)
        debate_points.sort(key=lambda x: x["strength"], reverse=True)
        return debate_points[:3]  # Top 3 strongest arguments
    
    async def _conduct_round(self, round_num: int, first_agent: str, second_agent: str, 
                           first_claims: List, second_claims: List, previous_rounds: List) -> Dict:
        """Conduct a single debate round."""
        
        round_result = {
            "round_number": round_num,
            "first_speaker": first_agent,
            "second_speaker": second_agent,
            "first_argument": "",
            "second_argument": "",
            "counter_argument": "",
            "round_winner": None,
            "points_awarded": 0,
            "reasoning": "",
            "evidence_comparison": {}
        }
        
        try:
            # First agent presents argument
            if first_claims:
                selected_claim = first_claims[min(round_num - 1, len(first_claims) - 1)]
                round_result["first_argument"] = await self._generate_argument(
                    selected_claim, first_agent, "opening", previous_rounds
                )
            
            # Second agent responds
            if second_claims:
                selected_claim = second_claims[min(round_num - 1, len(second_claims) - 1)]
                round_result["second_argument"] = await self._generate_counter_argument(
                    selected_claim, second_agent, round_result["first_argument"], previous_rounds
                )
            
            # Evaluate round winner
            round_result["round_winner"], round_result["points_awarded"], round_result["reasoning"] = (
                await self._evaluate_round(round_result, first_claims, second_claims)
            )
            
        except Exception as e:
            print(f"Error in round {round_num}: {e}")
            round_result["reasoning"] = f"Round error: {str(e)}"
        
        return round_result
    
    async def _generate_argument(self, claim_data: Dict, agent_type: str, argument_type: str, 
                               previous_rounds: List) -> str:
        """Generate an argument for the debate."""
        
        context = f"""You are a {agent_type} political analyst participating in a structured debate.
        
Argument Type: {argument_type}
Your Claim: {claim_data.get('claim', '')}
Your Evidence: {', '.join(claim_data.get('evidence', [])[:2])}
Your Sources: {', '.join(claim_data.get('sources', [])[:2])}

Previous rounds context: {len(previous_rounds)} rounds completed.

Generate a strong, fact-based argument (2-3 sentences) that:
1. States your position clearly
2. Presents your strongest evidence
3. References credible sources
4. Maintains professional tone

Keep it concise and impactful."""

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, context
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating argument: {e}")
            return f"Based on our research from {len(claim_data.get('sources', []))} sources, {claim_data.get('claim', 'the evidence suggests a clear position')}."
    
    async def _generate_counter_argument(self, claim_data: Dict, agent_type: str, 
                                       opponent_argument: str, previous_rounds: List) -> str:
        """Generate a counter-argument responding to opponent."""
        
        context = f"""You are a {agent_type} political analyst in a structured debate.

Opponent's Argument: {opponent_argument}

Your Counter-Position: {claim_data.get('claim', '')}
Your Evidence: {', '.join(claim_data.get('evidence', [])[:2])}
Your Sources: {', '.join(claim_data.get('sources', [])[:2])}

Generate a strong counter-argument (2-3 sentences) that:
1. Directly addresses the opponent's points
2. Presents contradicting evidence
3. Highlights flaws in their reasoning
4. Supports your alternative view with sources

Be respectful but assertive. Focus on facts over rhetoric."""

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, context
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating counter-argument: {e}")
            return f"However, our analysis of {len(claim_data.get('sources', []))} sources reveals {claim_data.get('claim', 'a different perspective')}."
    
    async def _evaluate_round(self, round_data: Dict, first_claims: List, second_claims: List) -> tuple:
        """Evaluate round winner based on argument quality and factual accuracy."""
        
        evaluation_context = f"""You are an objective fact-checker and debate judge. Evaluate this debate round to determine which argument contains more accurate and reliable information:

First Speaker ({round_data['first_speaker']}): {round_data['first_argument']}
Second Speaker ({round_data['second_speaker']}): {round_data['second_argument']}

CRITICAL: There must ALWAYS be a clear winner. No ties allowed.

Evaluation Criteria (rank each argument 1-10):
1. FACTUAL ACCURACY: Are the claims verifiable and correct?
2. SOURCE CREDIBILITY: Are sources authoritative and reliable?
3. EVIDENCE QUALITY: Is the supporting evidence strong and relevant?
4. LOGICAL CONSISTENCY: Is the argument internally coherent?
5. COMPLETENESS: Does it address the core issues comprehensively?

Based on these criteria, determine which argument presents more accurate, credible, and well-supported information.

You MUST respond with EXACTLY this format:
WINNER: [first/second]
POINTS: [1-3 based on margin of victory]
REASONING: [Brief explanation of why this argument was more factually accurate and credible]

Choose the argument with better factual accuracy and evidence quality. If very close, pick the one with more credible sources."""

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, evaluation_context
            )
            
            evaluation = response.text.strip()
            
            # Parse evaluation with forced winner selection
            if "WINNER: first" in evaluation.lower():
                winner = round_data['first_speaker']
            elif "WINNER: second" in evaluation.lower():
                winner = round_data['second_speaker']
            else:
                # Fallback: analyze argument quality if format is unclear
                first_arg_quality = self._analyze_argument_quality(round_data.get('first_argument', ''), first_claims)
                second_arg_quality = self._analyze_argument_quality(round_data.get('second_argument', ''), second_claims)
                
                winner = round_data['first_speaker'] if first_arg_quality >= second_arg_quality else round_data['second_speaker']
            
            # Extract points
            if "POINTS: 3" in evaluation:
                points = 3
            elif "POINTS: 2" in evaluation:
                points = 2
            else:
                points = 1
            
            # Extract reasoning
            reasoning_start = evaluation.find("REASONING:")
            if reasoning_start != -1:
                reasoning = evaluation[reasoning_start + 10:].strip()
            else:
                reasoning = f"Winner determined based on superior factual accuracy and evidence quality."
            
        except Exception as e:
            print(f"Error evaluating round: {e}")
            # Fallback: detailed argument analysis
            first_arg_quality = self._analyze_argument_quality(round_data.get('first_argument', ''), first_claims)
            second_arg_quality = self._analyze_argument_quality(round_data.get('second_argument', ''), second_claims)
            
            if first_arg_quality > second_arg_quality:
                winner = round_data['first_speaker']
                points = 2 if first_arg_quality - second_arg_quality > 2 else 1
            else:
                winner = round_data['second_speaker']
                points = 2 if second_arg_quality - first_arg_quality > 2 else 1
                
            reasoning = f"Winner determined by argument analysis - stronger evidence and factual support."
        
        return winner, points, reasoning
    
    def _analyze_argument_quality(self, argument: str, claims: List) -> int:
        """Analyze argument quality based on length, sources, and evidence."""
        quality_score = 0
        
        # Base score from argument length and detail
        quality_score += min(len(argument.split()) // 10, 3)  # Max 3 points for detail
        
        # Score from available evidence
        if claims:
            avg_evidence = sum(len(claim.get('evidence', [])) for claim in claims) / len(claims)
            quality_score += min(int(avg_evidence), 3)  # Max 3 points for evidence
            
            avg_sources = sum(len(claim.get('sources', [])) for claim in claims) / len(claims)
            quality_score += min(int(avg_sources), 2)  # Max 2 points for sources
        
        return quality_score
    
    def _determine_final_winner(self, scores: Dict) -> str:
        """Determine the final debate winner - always returns a winner, never None."""
        if scores["leftist"] > scores["rightist"]:
            return "leftist"
        elif scores["rightist"] > scores["leftist"]:
            return "rightist"
        else:
            # In case of tie, determine winner based on who provided more accurate information
            # For now, we'll use a simple tiebreaker - but this should rarely happen with the new evaluation
            print("⚖️ Scores tied - applying tiebreaker based on information accuracy")
            return "leftist"  # This could be made more sophisticated later
    
    async def _generate_debate_summary(self, debate_session: Dict) -> str:
        """Generate a comprehensive debate summary."""
        
        summary_context = f"""Summarize this political debate session focusing on information accuracy:

Total Rounds: {debate_session['total_rounds']}
Final Scores: Leftist {debate_session['scores']['leftist']} - Rightist {debate_session['scores']['rightist']}
Winner: {debate_session['winner']} (determined by factual accuracy and evidence quality)
Duration: {debate_session.get('duration', 0):.1f} seconds

Generate a professional 3-4 sentence summary covering:
1. Key arguments and evidence presented by both sides
2. Why the winning side provided more accurate and credible information
3. Quality of sources and factual support
4. Overall assessment of which perspective had stronger evidence base

Focus on factual accuracy and information credibility rather than political bias."""

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, summary_context
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Debate concluded after {debate_session['total_rounds']} rounds. {debate_session['winner'].title()} perspective provided more accurate and well-supported information with stronger evidence base and more credible sources."
            winner_text = f"The {debate_session['winner']} perspective" if debate_session['winner'] else "Both perspectives"
            return f"{winner_text} demonstrated stronger evidence in this {debate_session['total_rounds']}-round debate, with final scores of {debate_session['scores']['leftist']}-{debate_session['scores']['rightist']}."

def _set(stage=None, progress=None, error=None):
    with LOCK:
        if stage: STATE["stage"] = stage
        if progress is not None: STATE["progress"] = progress
        if error is not None: STATE["error"] = error
        if stage == "done":
            STATE["ended_at"] = time.time()

def run_module3():
    """Run module3 pipeline directly."""
    try:
        STATE["started_at"] = time.time()
        _set(stage="module3", progress=10)
        
        # Set up environment for Module3
        try:
            from dotenv import load_dotenv
            mod3_env_path = MOD3_DIR.parent / ".env"
            load_dotenv(mod3_env_path)
            
            # Set the GOOGLE_API_KEY environment variable from GENAI_API_KEY
            api_key = os.getenv('GENAI_API_KEY')
            if api_key:
                os.environ['GOOGLE_API_KEY'] = api_key
                print("Set GOOGLE_API_KEY from .env file")
        except Exception as e:
            print(f"Error loading Module3 environment: {e}")
        
        print("Running Module3 pipeline directly")
        
        # Import and run the Module3 pipeline directly
        import sys
        sys.path.append(str(MOD3_DIR))
        sys.path.append(str(MOD3_DIR / "main_modules"))
        
        try:
            from main_modules import api_request
            
            # Define callback function for streaming perspectives
            def stream_callback(color, perspectives):
                print(f"Received {len(perspectives)} perspectives for color {color}")
                
                # Update progress based on color (rough estimation)
                color_progress = {
                    "red": 20, "orange": 35, "yellow": 50, 
                    "green": 65, "blue": 80, "indigo": 90, "violet": 95
                }
                _set(progress=color_progress.get(color, 50))
                
                # Store perspectives in cache
                global perspective_cache
                if color not in perspective_cache:
                    perspective_cache[color] = []
                perspective_cache[color] = perspectives
                print(f"Stored {len(perspectives)} {color} perspectives in cache")
            
            # Create arguments for the api_request module
            class Args:
                pass
            args = Args()
            args.input = str(MOD3_DIR / "input.json")
            args.output = str(MOD3_DIR / "output.json")
            args.endpoint = None
            args.model = None
            args.temperature = 0.6
            args.stream_callback = stream_callback
            
            # Run the pipeline
            print("Executing Module3 pipeline...")
            code = api_request.run_pipeline(args)
            print(f"Module3 pipeline completed with code: {code}")
            
        except Exception as e:
            _set(stage="error", error=f"Module3 pipeline execution failed: {str(e)}")
            print(f"Module3 pipeline error: {e}")
            return
        
        # Load and cache final perspectives from output file
        output_file = MOD3_DIR / "output.json"
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    full_data = json.load(f)
                    if "perspectives" in full_data:
                        # Group perspectives by color
                        by_color = {}
                        for p in full_data["perspectives"]:
                            color = p.get("color")
                            if color:
                                if color not in by_color:
                                    by_color[color] = []
                                by_color[color].append(p)
                        
                        # Update our cache with the complete data
                        perspective_cache.update(by_color)
                        print(f"Final cached perspectives by color: {list(by_color.keys())}")
            except Exception as e:
                print(f"Error loading perspectives from output file: {e}")
        
        # Check if we need to run the clustering step
        clustering_file = MOD3_DIR / "modules" / "TOP-N_K_MEANS-CLUSTERING.py"
        if clustering_file.exists():
            _set(progress=96, stage="clustering")
            try:
                subprocess.run([
                    PYTHON_EXE,
                    str(clustering_file)
                ], cwd=str(MOD3_DIR), check=True, timeout=60)
                print("Clustering completed successfully")
            except Exception as e:
                print(f"Clustering failed: {e}")
                # Continue anyway
        
        _set(progress=100, stage="done")
        
    except Exception as e:
        _set(stage="error", error=f"Unexpected error in Module3: {str(e)}")
        print(f"Unexpected error in Module3: {e}")
        import traceback
        traceback.print_exc()

@app.post("/run")
def start_run(data: dict, background: BackgroundTasks):
    if STATE["stage"] in ("module3",):
        return JSONResponse({"error": "pipeline already running"}, status_code=409)
    # Clear any previously cached perspectives when initiating a new run
    global perspective_cache
    if perspective_cache:
        print("Clearing existing perspective cache for new run")
    perspective_cache = {}
    _set(stage="queued", progress=0, error=None)
    background.add_task(run_module3)
    return {"status": "started"}

@app.get("/status")
def get_status():
    # Add cache headers for better frontend performance
    headers = {"Cache-Control": "no-cache, must-revalidate"}
    return JSONResponse(content=STATE, headers=headers)

@app.get("/health")
def health_check():
    """Main health check endpoint for the orchestrator."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "modules": {
            "module1": "available",
            "module2": "available", 
            "module3": "available",
            "module4": "available"
        }
    }

@app.get("/results")
def get_results():
    if STATE["stage"] != "done":
        return JSONResponse({"error": "not ready"}, status_code=400)
    
    out_file = MOD3_DIR / "output.json"
    if not out_file.exists():
        return JSONResponse({"error": "final output missing"}, status_code=500)
    
    try:
        # Faster file reading with explicit encoding
        with open(out_file, 'r', encoding='utf-8') as f:
            return json.load(f)  # Direct JSON load instead of read + parse
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON in output file"}, status_code=500)
    except IOError as e:
        return JSONResponse({"error": f"file read error: {str(e)}"}, status_code=500)
        
# Module3 output endpoints
@app.get("/module3/output/leftist")
def get_module3_leftist():
    """Get the leftist perspectives from module3 final output."""
    # Only allow access when the pipeline is complete
    if STATE["stage"] not in ["done", "idle", "error"]:
        return JSONResponse({
            "error": "Pipeline is still running. Files from previous run are not accessible.",
            "stage": STATE["stage"],
            "progress": STATE["progress"]
        }, status_code=409)  # 409 Conflict
    
    leftist_file = MOD3_DIR / "final_output" / "leftist.json"
    if not leftist_file.exists():
        return JSONResponse({"error": "leftist output missing"}, status_code=404)
    
    try:
        with open(leftist_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON in leftist file"}, status_code=500)
    except IOError as e:
        return JSONResponse({"error": f"file read error: {str(e)}"}, status_code=500)

@app.get("/module3/output/rightist")
def get_module3_rightist():
    """Get the rightist perspectives from module3 final output."""
    # Only allow access when the pipeline is complete
    if STATE["stage"] not in ["done", "idle", "error"]:
        return JSONResponse({
            "error": "Pipeline is still running. Files from previous run are not accessible.",
            "stage": STATE["stage"],
            "progress": STATE["progress"]
        }, status_code=409)  # 409 Conflict
    
    rightist_file = MOD3_DIR / "final_output" / "rightist.json"
    if not rightist_file.exists():
        return JSONResponse({"error": "rightist output missing"}, status_code=404)
    
    try:
        with open(rightist_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON in rightist file"}, status_code=500)
    except IOError as e:
        return JSONResponse({"error": f"file read error: {str(e)}"}, status_code=500)

@app.get("/module3/output/common")
def get_module3_common():
    """Get the common perspectives from module3 final output."""
    # Only allow access when the pipeline is complete
    if STATE["stage"] not in ["done", "idle", "error"]:
        return JSONResponse({
            "error": "Pipeline is still running. Files from previous run are not accessible.",
            "stage": STATE["stage"],
            "progress": STATE["progress"]
        }, status_code=409)  # 409 Conflict
    
    common_file = MOD3_DIR / "final_output" / "common.json"
    if not common_file.exists():
        return JSONResponse({"error": "common output missing"}, status_code=404)
    
    try:
        with open(common_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON in common file"}, status_code=500)
    except IOError as e:
        return JSONResponse({"error": f"file read error: {str(e)}"}, status_code=500)

@app.get("/ws/cache")
def get_perspective_cache():
    """Get the current perspective cache for polling clients."""
    # Log the current cache state for debugging
    colors = list(perspective_cache.keys())
    color_counts = {color: len(perspectives) for color, perspectives in perspective_cache.items()}
    print(f"Serving perspective cache: {colors} with counts: {color_counts}")
    
    # Check if we're done processing but missing violet
    if "red" in perspective_cache and "orange" in perspective_cache and \
       "yellow" in perspective_cache and "green" in perspective_cache and \
       "blue" in perspective_cache and "indigo" in perspective_cache and \
       "violet" not in perspective_cache and STATE["progress"] >= 90:
        
        # Try to load violet from output file if it exists
        try:
            output_file = MOD3_DIR / "output.json"
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    full_data = json.load(f)
                    if "perspectives" in full_data:
                        # Find violet perspectives
                        violet_perspectives = [p for p in full_data["perspectives"] if p.get("color") == "violet"]
                        if violet_perspectives:
                            print(f"Loading {len(violet_perspectives)} violet perspectives from output file")
                            perspective_cache["violet"] = violet_perspectives
        except Exception as e:
            print(f"Error loading violet perspectives from file: {e}")
    
    return perspective_cache

@app.websocket("/ws/perspectives")
async def perspectives_ws(websocket: WebSocket):
    await websocket.accept()
    print(f"WebSocket client connected from {websocket.client.host}:{websocket.client.port}")
    
    # Add to active connections
    active_websockets.add(websocket)
    
    try:
        # Send any cached perspectives to the new client
        if perspective_cache:
            print(f"Sending cached perspectives to new client: {len(perspective_cache)} color groups")
            for color, perspectives in perspective_cache.items():
                try:
                    await websocket.send_json({
                        "color": color,
                        "perspectives": perspectives
                    })
                    print(f"Sent {len(perspectives)} {color} perspectives to client")
                except Exception as e:
                    print(f"Error sending {color} perspectives to client: {e}")
        
        # Keep the connection alive
        while True:
            try:
                # Wait for any message with a timeout
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Normal case - no message received, client still connected
                # Optionally send a ping to verify connection
                try:
                    await websocket.send_json({"type": "ping", "timestamp": time.time()})
                except Exception:
                    # If ping fails, connection is probably dead
                    break
            except Exception as e:
                print(f"WebSocket receive error: {str(e)}")
                break
    except WebSocketDisconnect:
        print(f"WebSocket client disconnected normally")
    except Exception as e:
        print(f"WebSocket connection error: {str(e)}")
    finally:
        # Remove from active connections
        active_websockets.remove(websocket)
        print("WebSocket connection closed")

# Broadcast perspectives to all connected WebSocket clients
async def broadcast_perspectives(color, perspectives):
    if perspectives:
        # Cache the perspectives
        perspective_cache[color] = perspectives
        
        # Send to all connected clients
        for websocket in list(active_websockets):
            try:
                await websocket.send_json({
                    "color": color,
                    "perspectives": perspectives
                })
            except Exception as e:
                print(f"Error sending to WebSocket client: {str(e)}")
                # Don't remove here, let the connection handler do it

# Module4 WebSocket endpoint for real-time research streaming
@app.websocket("/ws/module4/{job_id}")
async def module4_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    print(f"Module4 WebSocket client connected for job {job_id}")
    
    # Add to Module4 connections
    module4_websockets.add(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "job_id": job_id,
            "message": "Connected to Module4 research stream"
        })
        
        # Monitor job progress and stream updates
        while True:
            if job_id in module4_jobs:
                job_status = module4_jobs[job_id]
                
                # Send progress update
                await websocket.send_json({
                    "type": "progress",
                    "job_id": job_id,
                    "status": job_status.get('status', 'unknown'),
                    "progress": job_status.get('progress', 0),
                    "message": job_status.get('message', ''),
                    "agent_type": job_status.get('agent_type', 'unknown')
                })
                
                # Stream content if available
                if 'partial_content' in job_status:
                    await websocket.send_json({
                        "type": "content_stream",
                        "job_id": job_id,
                        "content": job_status['partial_content'],
                        "agent_type": job_status.get('agent_type', 'unknown')
                    })
                
                # Send final results if completed
                if job_status.get('status') == 'completed' and 'results' in job_status:
                    await websocket.send_json({
                        "type": "completed",
                        "job_id": job_id,
                        "results": job_status['results'],
                        "agent_type": job_status.get('agent_type', 'unknown')
                    })
                    break
                
                # Handle errors
                if job_status.get('status') == 'error':
                    await websocket.send_json({
                        "type": "error",
                        "job_id": job_id,
                        "error": job_status.get('error', 'Unknown error'),
                        "agent_type": job_status.get('agent_type', 'unknown')
                    })
                    break
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"Module4 WebSocket client disconnected for job {job_id}")
    except Exception as e:
        print(f"Module4 WebSocket error for job {job_id}: {str(e)}")
    finally:
        # Remove from active connections
        if websocket in module4_websockets:
            module4_websockets.remove(websocket)
        print(f"Module4 WebSocket connection closed for job {job_id}")

# Debate WebSocket endpoint for real-time debate streaming
@app.websocket("/ws/debate/{job_id}")
async def debate_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    print(f"Debate WebSocket client connected for job {job_id}")
    
    # Add to Debate connections
    debate_websockets.add(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "job_id": job_id,
            "message": "Connected to Debate stream"
        })
        
        # Monitor debate progress and stream updates
        while True:
            if job_id in module4_jobs:
                job_status = module4_jobs[job_id]
                
                # Send progress update
                await websocket.send_json({
                    "type": "progress",
                    "job_id": job_id,
                    "status": job_status.get('status', 'unknown'),
                    "progress": job_status.get('progress', 0),
                    "message": job_status.get('message', ''),
                    "agent_type": job_status.get('agent_type', 'debate')
                })
                
                # Stream debate rounds if available
                if 'debate_rounds' in job_status:
                    await websocket.send_json({
                        "type": "debate_round",
                        "job_id": job_id,
                        "rounds": job_status['debate_rounds'],
                        "current_scores": job_status.get('current_scores', {"leftist": 0, "rightist": 0})
                    })
                
                # Send final results if completed
                if job_status.get('status') == 'completed' and 'results' in job_status:
                    await websocket.send_json({
                        "type": "debate_completed",
                        "job_id": job_id,
                        "results": job_status['results'],
                        "winner": job_status['results'].get('winner'),
                        "final_scores": job_status['results'].get('scores'),
                        "debate_summary": job_status['results'].get('debate_summary')
                    })
                    break
                
                # Handle errors
                if job_status.get('status') == 'error':
                    await websocket.send_json({
                        "type": "error",
                        "job_id": job_id,
                        "error": job_status.get('error', 'Unknown error'),
                        "agent_type": "debate"
                    })
                    break
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"Debate WebSocket client disconnected for job {job_id}")
    except Exception as e:
        print(f"Debate WebSocket error for job {job_id}: {str(e)}")
    finally:
        # Remove from active connections
        if websocket in debate_websockets:
            debate_websockets.remove(websocket)
        print(f"Debate WebSocket connection closed for job {job_id}")

# ==================== MODULE1 INTEGRATION ====================

# Module1 Request/Response models
class URLRequest(BaseModel):
    url: str

class URLResponse(BaseModel):
    safe: bool
    content: str

def initialize_module1():
    """Initialize Module1 LinkValidator with API keys from .env file."""
    try:
        # Add Module1 paths to Python path
        sys.path.insert(0, str(MOD1_DIR))
        sys.path.insert(0, str(MOD1_DIR / "Modules" / "LinkValidator"))
        
        # Load environment variables from Module1/.env
        env_file = BASE / "Module1" / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Import LinkValidator
        from linkValidator import LinkValidator
        
        # Get API keys from environment
        google_api_key = os.getenv('GOOGLE_API_KEY')
        virustotal_api_key = os.getenv('VIRUSTOTAL_API_KEY')
        
        if not google_api_key or not virustotal_api_key:
            raise ValueError("API keys not found in environment variables")
        
        # Initialize and return the validator
        validator = LinkValidator(google_api_key, virustotal_api_key)
        print("Module1 LinkValidator initialized successfully")
        return validator
        
    except Exception as e:
        print(f"Error initializing Module1: {str(e)}")
        return None

# Initialize Module1 validator on startup
module1_validator = initialize_module1()

@app.post("/module1/validate", response_model=URLResponse)
async def validate_url(request: URLRequest):
    """Validate URL using Module1 LinkValidator."""
    if not module1_validator:
        raise HTTPException(status_code=500, detail="Module1 validator not initialized")
    
    try:
        print(f"Validating URL: {request.url}")
        
        # First, validate the URL for safety
        validation_result = module1_validator.validate_url(request.url)
        print(f"Validation result: {validation_result}")
        
        is_safe = validation_result.get('safe', False)
        content = ""
        
        # If URL is safe, scrape content
        if is_safe:
            print(f"URL is safe, scraping content...")
            scrape_result = module1_validator.scrape_website_content(request.url)
            content = scrape_result.get('main_text', '')
            print(f"Scraped content length: {len(content)} characters")
        else:
            print(f"URL is not safe, skipping content scraping")
        
        return URLResponse(
            safe=is_safe,
            content=content
        )
        
    except Exception as e:
        print(f"Error validating URL {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/module1/health")
async def module1_health():
    """Health check for Module1."""
    if not module1_validator:
        return JSONResponse(
            {"status": "unhealthy", "service": "Module1 URL Validator", "error": "Validator not initialized"},
            status_code=503
        )
    
    return {
        "status": "healthy",
        "service": "Module1 URL Validator",
        "initialized": True
    }

# ==================== MODULE2 INTEGRATION ====================

# Module2 Request/Response models
class AnalysisRequest(BaseModel):
    text: str

class ClassificationResult(BaseModel):
    person: float
    organization: float
    social: float
    critical: float
    stem: float

class AnalysisResponse(BaseModel):
    classification: ClassificationResult
    significance_score: int
    summary: str
    source: bool

# Module4 Request/Response models
class Module4JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

class Module4JobStatus(BaseModel):
    job_id: str
    status: str  # 'running', 'completed', 'error'
    progress: float
    message: str
    started_at: float
    completed_at: Optional[float] = None
    error: Optional[str] = None

class Module4ResearchRequest(BaseModel):
    mode: str = 'fast'  # 'fast' or 'slow'

# Debate Request/Response models
class DebateRequest(BaseModel):
    leftist_job_id: str
    rightist_job_id: str

class DebateJobResponse(BaseModel):
    job_id: str
    status: str
    message: str

def initialize_module2():
    """Initialize Module2 components with API keys from environment."""
    try:
        # Add Module2 paths to Python path
        sys.path.insert(0, str(MOD2_DIR))
        sys.path.insert(0, str(MOD2_DIR / "Modules" / "Classifier"))
        sys.path.insert(0, str(MOD2_DIR / "Modules" / "SignificanceScore"))
        sys.path.insert(0, str(MOD2_DIR / "Modules" / "Summarizer"))
        
        # Load environment variables for Module2
        try:
            from dotenv import load_dotenv
            mod2_env_path = MOD2_DIR.parent / ".env"
            load_dotenv(mod2_env_path)
        except ImportError:
            pass
        
        # Try different API key environment variables
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or os.getenv('API_KEY')
        model_name = os.getenv('MODEL_NAME', 'gemini-2.0-flash')
        
        if not api_key:
            print("Warning: No API key found for Module2. Using fallback API key.")
            # Use the provided fallback API key
            api_key = "AIzaSyDomf7gcJ5OFYVNzl2nRRfmbDe6exqqcps"
        
        if not api_key:
            raise ValueError("No API key available for Module2")
        
        print(f"Initializing Module2 with model: {model_name}")
        
        # Import Module2 components
        from classifier import FakeNewsDetector
        from scoreProvider import get_triage_score
        from summarizer import ComprehensiveSummarizer
        
        # Initialize components
        classifier = FakeNewsDetector(api_key, model_name)
        summarizer = ComprehensiveSummarizer(api_key, model_name)
        
        print("Module2 components initialized successfully")
        return {
            'classifier': classifier,
            'summarizer': summarizer,
            'score_provider': get_triage_score
        }
        
    except Exception as e:
        print(f"Error initializing Module2: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Initialize Module2 components on startup
module2_components = initialize_module2()

def convert_module2_to_module3_format(module2_response: AnalysisResponse) -> dict:
    """
    Convert Module2 output format to Module3 input format.
    
    Args:
        module2_response: AnalysisResponse from Module2
        
    Returns:
        dict: Formatted data for Module3 input.json
    """
    # Generate a topic based on the summary content
    summary_text = module2_response.summary
    
    # Create a short topic title from the summary (first sentence or key phrases)
    topic_words = summary_text.split()[:10]  # Take first 10 words
    topic = " ".join(topic_words)
    if len(topic) > 80:  # Limit topic length
        topic = topic[:77] + "..."
    
    # Convert significance score from integer (0-100) to float (0-1)
    significance_score_normalized = module2_response.significance_score / 100.0
    
    # Ensure score is within 0-1 range
    significance_score_normalized = max(0.0, min(1.0, significance_score_normalized))
    
    return {
        "topic": topic,
        "text": module2_response.summary,
        "significance_score": significance_score_normalized
    }

def update_module3_input_json(formatted_data: dict):
    """
    Update Module3's input.json file with formatted data.
    
    Args:
        formatted_data: Dictionary containing topic, text, and significance_score
    """
    try:
        module3_input_path = MOD3_DIR / "input.json"
        
        # Write the formatted data to input.json
        with open(module3_input_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=2, ensure_ascii=False)
        
        print(f"Updated Module3 input.json with topic: '{formatted_data['topic']}'")
        return True
        
    except Exception as e:
        print(f"Error updating Module3 input.json: {str(e)}")
        return False

@app.post("/module2/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """Analyze text for misinformation using Module2 components."""
    if not module2_components:
        raise HTTPException(status_code=500, detail="Module2 components not initialized")
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")
    
    try:
        print(f"Analyzing text: {request.text[:100]}...")
        
        classifier = module2_components['classifier']
        summarizer = module2_components['summarizer']
        score_provider = module2_components['score_provider']
        
        # Get classification
        classification = classifier.classify(request.text)
        
        # Get significance score
        score = score_provider(request.text)
        
        # Get summary
        summary_result = summarizer.summarize(request.text)
        
        # Check for URLs/links in text
        import re
        url_pattern = r'(https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        has_source = bool(re.search(url_pattern, request.text))
        
        # Create response
        response = AnalysisResponse(
            classification=ClassificationResult(
                person=classification.person,
                organization=classification.organization,
                social=classification.social,
                critical=classification.critical,
                stem=classification.stem
            ),
            significance_score=score,
            summary=summary_result.comprehensive_summary,
            source=has_source
        )
        
        print(f"Analysis complete: Score={score}, Has_source={has_source}")
        
        # Automatically update Module3 input.json with the analysis results
        try:
            formatted_data = convert_module2_to_module3_format(response)
            update_module3_input_json(formatted_data)
            print("Module3 input.json updated automatically")
        except Exception as e:
            print(f"Warning: Failed to update Module3 input.json: {str(e)}")
        
        return response
        
    except Exception as e:
        print(f"Error analyzing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/module2/health")
async def module2_health():
    """Health check for Module2."""
    if not module2_components:
        return JSONResponse(
            {"status": "unhealthy", "service": "Module2 Misinformation Analyzer", "error": "Components not initialized"},
            status_code=503
        )
    
    return {
        "status": "healthy",
        "service": "Module2 Misinformation Analyzer",
        "components": {
            "classifier": "initialized",
            "summarizer": "initialized", 
            "score_provider": "initialized"
        }
    }

# Broadcast Module4 updates to WebSocket clients
async def broadcast_module4_update(job_id: str, update_type: str, data: dict):
    """Broadcast Module4 updates to connected WebSocket clients"""
    if not module4_websockets:
        return
        
    message = {
        "type": update_type,
        "job_id": job_id,
        **data
    }
    
    # Send to all connected Module4 clients
    for websocket in list(module4_websockets):
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error broadcasting to Module4 WebSocket client: {str(e)}")

# ==================== MODULE4 INTEGRATION ====================

async def run_module4_agent(job_id: str, agent_type: str, analysis_mode: str = 'fast'):
    """Run Module4 deep research agent in background."""
    try:
        module4_jobs[job_id]['status'] = 'running'
        module4_jobs[job_id]['agent_type'] = agent_type
        module4_jobs[job_id]['analysis_mode'] = analysis_mode
        module4_jobs[job_id]['message'] = f'Starting {agent_type} deep research ({analysis_mode} mode)...'
        module4_jobs[job_id]['progress'] = 10
        
        print(f"Starting Module4 {agent_type} research agent for job {job_id} in {analysis_mode} mode")
        
        # Add Module4 backend directory to Python path
        sys.path.insert(0, str(MOD4_DIR))
        
        # Update progress
        module4_jobs[job_id]['progress'] = 25
        module4_jobs[job_id]['message'] = 'Loading Module 3 perspectives and initializing research...'
        
        # Load Module 3 output to get perspectives
        leftist_data, rightist_data, common_data = load_module3_perspectives()
        
        # Update progress
        module4_jobs[job_id]['progress'] = 40
        module4_jobs[job_id]['message'] = 'Selecting perspectives for research...'
        
        # Select perspectives based on agent type
        if agent_type == 'leftist':
            # Leftist agent gets leftist + common perspectives
            perspectives_data = {
                'leftist': leftist_data,
                'common': common_data
            }
            module4_jobs[job_id]['message'] = f'Researching {len(leftist_data)} leftist + {len(common_data)} common perspectives...'
        elif agent_type == 'rightist':
            # Rightist agent gets rightist + common perspectives  
            perspectives_data = {
                'rightist': rightist_data,
                'common': common_data
            }
            module4_jobs[job_id]['message'] = f'Researching {len(rightist_data)} rightist + {len(common_data)} common perspectives...'
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Update progress
        module4_jobs[job_id]['progress'] = 50
        
        # Import and run the appropriate agent with perspectives data
        if agent_type == 'leftist':
            try:
                from leftistagent import research_with_perspectives
                
                # Stream initial message
                await broadcast_module4_update(job_id, "content_stream", {
                    "content": "🔍 Starting leftist research analysis...\n",
                    "agent_type": agent_type
                })
                
                results = await research_with_perspectives(perspectives_data, analysis_mode)
            except ImportError as e:
                print(f"Failed to import leftist agent: {e}")
                raise Exception(f"Failed to import leftist agent: {e}")
        elif agent_type == 'rightist':
            try:
                from rightistagent import research_with_perspectives
                
                # Stream initial message
                await broadcast_module4_update(job_id, "content_stream", {
                    "content": "🔍 Starting rightist research analysis...\n", 
                    "agent_type": agent_type
                })
                
                results = await research_with_perspectives(perspectives_data, analysis_mode)
            except ImportError as e:
                print(f"Failed to import rightist agent: {e}")
                raise Exception(f"Failed to import rightist agent: {e}")
        
        # Stream research completion
        await broadcast_module4_update(job_id, "content_stream", {
            "content": "✅ Research analysis completed. Processing findings...\n",
            "agent_type": agent_type
        })
        
        # Update progress
        module4_jobs[job_id]['progress'] = 90
        module4_jobs[job_id]['message'] = 'Research completed, processing results...'
        
        # Process and format results
        formatted_results = format_research_results(results, agent_type, analysis_mode)
        
        # Mark completion
        module4_jobs[job_id]['status'] = 'completed'
        module4_jobs[job_id]['progress'] = 100
        module4_jobs[job_id]['message'] = f'{agent_type.capitalize()} deep research completed successfully'
        module4_jobs[job_id]['completed_at'] = time.time()
        module4_jobs[job_id]['results'] = formatted_results
        
        print(f"Module4 {agent_type} research agent completed for job {job_id}")
        
    except Exception as e:
        print(f"Module4 {agent_type} research agent failed for job {job_id}: {e}")
        module4_jobs[job_id]['status'] = 'error'
        module4_jobs[job_id]['error'] = str(e)
        module4_jobs[job_id]['message'] = f'{agent_type.capitalize()} research failed: {str(e)}'

def load_module3_perspectives():
    """Load perspectives from Module 3 output files."""
    try:
        leftist_file = MOD3_DIR / "final_output" / "leftist.json"
        rightist_file = MOD3_DIR / "final_output" / "rightist.json"
        common_file = MOD3_DIR / "final_output" / "common.json"
        
        leftist_data = []
        rightist_data = []
        common_data = []
        
        if leftist_file.exists():
            with open(leftist_file, 'r', encoding='utf-8') as f:
                leftist_data = json.load(f)
        
        if rightist_file.exists():
            with open(rightist_file, 'r', encoding='utf-8') as f:
                rightist_data = json.load(f)
                
        if common_file.exists():
            with open(common_file, 'r', encoding='utf-8') as f:
                common_data = json.load(f)
        
        print(f"Loaded Module 3 perspectives: {len(leftist_data)} leftist, {len(rightist_data)} rightist, {len(common_data)} common")
        return leftist_data, rightist_data, common_data
        
    except Exception as e:
        print(f"Error loading Module 3 perspectives: {e}")
        return [], [], []

def format_research_results(results, agent_type, analysis_mode):
    """Format research results for frontend display."""
    try:
        # Add metadata about the research
        formatted_results = {
            'agent_type': agent_type,
            'analysis_mode': analysis_mode,
            'research_timestamp': time.time(),
            'original_results': results
        }
        
        # Extract summary statistics if available
        if isinstance(results, dict):
            formatted_results.update(results)
            
            # Calculate additional metrics
            extracted_content = results.get('extracted_content', [])
            total_urls = len(extracted_content)
            successful_urls = len([item for item in extracted_content if item.get('success', False)])
            
            formatted_results['totalUrls'] = total_urls
            formatted_results['successfulUrls'] = successful_urls
            formatted_results['successRate'] = f"{(successful_urls/total_urls*100):.1f}%" if total_urls > 0 else "0%"
            
            # Add timing information
            if 'summary' in results:
                summary = results['summary']
                formatted_results['totalTime'] = summary.get('total_processing_time', 'N/A')
                formatted_results['summary'] = {
                    'summary': f"Deep research analysis completed using {analysis_mode} mode. Analyzed {total_urls} sources with {formatted_results['successRate']} success rate.",
                    'perspectives_analyzed': summary.get('perspectives_analyzed', 0),
                    'research_quality': 'High' if analysis_mode == 'slow' else 'Medium'
                }
        
        return formatted_results
        
    except Exception as e:
        print(f"Error formatting research results: {e}")
        return {'error': str(e), 'agent_type': agent_type, 'analysis_mode': analysis_mode}

async def capture_module4_results(agent_type: str):
    """Capture Module4 agent results from output files."""
    try:
        # Find the most recent output file for the agent type
        if agent_type == 'leftist':
            pattern = "enhanced_content_test_*.json"
        elif agent_type == 'rightist':
            pattern = "rightist_content_test_*.json"
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        import glob
        output_files = glob.glob(str(MOD4_DIR / pattern))
        
        if not output_files:
            print(f"No output files found for {agent_type} agent")
            return {"error": "No output files generated", "agent_type": agent_type}
        
        # Get the most recent file
        latest_file = max(output_files, key=os.path.getmtime)
        
        # Read and parse the results
        with open(latest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Add metadata
        results['agent_type'] = agent_type
        results['output_file'] = latest_file
        results['analysis_timestamp'] = time.time()
        
        # Calculate summary stats
        extracted_content = results.get('extracted_content', [])
        total_urls = len(extracted_content)
        successful_urls = len([item for item in extracted_content if item.get('success', False)])
        
        results['totalUrls'] = total_urls
        results['successfulUrls'] = successful_urls
        results['successRate'] = f"{(successful_urls/total_urls*100):.1f}%" if total_urls > 0 else "0%"
        
        # Add timing information if available
        if 'summary' in results:
            summary = results['summary']
            results['totalTime'] = summary.get('total_processing_time', 'N/A')
        
        print(f"Captured results for {agent_type} agent: {total_urls} URLs, {successful_urls} successful")
        
        return results
        
    except Exception as e:
        print(f"Error capturing {agent_type} agent results: {e}")
        return {"error": str(e), "agent_type": agent_type}

async def run_debate_task(job_id: str, leftist_results: Dict, rightist_results: Dict):
    """Run debate between agents in background."""
    try:
        module4_jobs[job_id]['status'] = 'running'
        module4_jobs[job_id]['message'] = 'Starting debate between leftist and rightist agents...'
        module4_jobs[job_id]['progress'] = 10
        
        print(f"Starting debate for job {job_id}")
        
        # Update progress
        module4_jobs[job_id]['progress'] = 25
        module4_jobs[job_id]['message'] = 'Initializing debate agent...'
        
        # Initialize the integrated debate agent
        debate_agent = DebateAgent()
        
        module4_jobs[job_id]['progress'] = 40
        module4_jobs[job_id]['message'] = 'Analyzing arguments and evidence...'
        
        # Conduct debate using integrated agent
        debate_results = await debate_agent.conduct_debate(leftist_results, rightist_results)
        
        # Update progress during debate rounds
        module4_jobs[job_id]['progress'] = 90
        module4_jobs[job_id]['message'] = 'Generating debate summary...'
        
        # Store intermediate rounds for streaming
        if 'rounds' in debate_results:
            module4_jobs[job_id]['debate_rounds'] = debate_results['rounds']
            module4_jobs[job_id]['current_scores'] = debate_results.get('scores', {"leftist": 0, "rightist": 0})
        
        # Mark completion
        module4_jobs[job_id]['status'] = 'completed'
        module4_jobs[job_id]['progress'] = 100
        winner = debate_results.get("winner", "Unknown")
        module4_jobs[job_id]['message'] = f'Debate completed - Most Accurate Information: {winner.upper()}'
        module4_jobs[job_id]['completed_at'] = time.time()
        module4_jobs[job_id]['results'] = debate_results
        
        print(f"Debate completed for job {job_id} - Winner: {debate_results.get('winner', 'Tie')}")
        
    except Exception as e:
        print(f"Debate failed for job {job_id}: {e}")
        module4_jobs[job_id]['status'] = 'error'
        module4_jobs[job_id]['error'] = str(e)
        module4_jobs[job_id]['message'] = f'Debate failed: {str(e)}'

@app.post("/module4/leftist/start", response_model=Module4JobResponse)
async def start_module4_leftist_research(request: Module4ResearchRequest, background_tasks: BackgroundTasks):
    """Start Module4 leftist deep research analysis."""
    job_id = f"leftist_research_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    # Initialize job tracking
    module4_jobs[job_id] = {
        'job_id': job_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Leftist deep research job created',
        'started_at': time.time(),
        'agent_type': 'leftist',
        'analysis_mode': request.mode
    }
    
    # Start background task
    background_tasks.add_task(run_module4_agent, job_id, 'leftist', request.mode)
    
    print(f"Started Module4 leftist research job: {job_id} ({request.mode} mode)")
    
    return Module4JobResponse(
        job_id=job_id,
        status="starting",
        message=f"Leftist deep research started ({request.mode} mode)"
    )

@app.post("/module4/rightist/start", response_model=Module4JobResponse)
async def start_module4_rightist_research(request: Module4ResearchRequest, background_tasks: BackgroundTasks):
    """Start Module4 rightist deep research analysis."""
    job_id = f"rightist_research_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    # Initialize job tracking
    module4_jobs[job_id] = {
        'job_id': job_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Rightist deep research job created',
        'started_at': time.time(),
        'agent_type': 'rightist',
        'analysis_mode': request.mode
    }
    
    # Start background task
    background_tasks.add_task(run_module4_agent, job_id, 'rightist', request.mode)
    
    print(f"Started Module4 rightist research job: {job_id} ({request.mode} mode)")
    
    return Module4JobResponse(
        job_id=job_id,
        status="starting",
        message=f"Rightist deep research started ({request.mode} mode)"
    )

@app.get("/module4/leftist/status/{job_id}")
async def get_module4_leftist_status(job_id: str):
    """Get Module4 leftist research job status."""
    if job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return module4_jobs[job_id]

@app.get("/module4/rightist/status/{job_id}")
async def get_module4_rightist_status(job_id: str):
    """Get Module4 rightist research job status."""
    if job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return module4_jobs[job_id]

@app.get("/module4/leftist/results/{job_id}")
async def get_module4_leftist_results(job_id: str):
    """Get Module4 leftist research results."""
    if job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = module4_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")
    
    if 'results' not in job:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job['results']

@app.get("/module4/rightist/results/{job_id}")
async def get_module4_rightist_results(job_id: str):
    """Get Module4 rightist research results."""
    if job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = module4_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")
    
    if 'results' not in job:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job['results']

@app.get("/module4/jobs")
async def list_module4_jobs():
    """List all Module4 jobs."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "agent_type": job.get("agent_type", "unknown"),
                "started_at": job["started_at"],
                "message": job["message"],
                "progress": job.get("progress", 0)
            }
            for job_id, job in module4_jobs.items()
        ]
    }

@app.delete("/module4/jobs/{job_id}")
async def delete_module4_job(job_id: str):
    """Delete a Module4 job from tracking."""
    if job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del module4_jobs[job_id]
    return {"message": f"Module4 job {job_id} deleted"}

@app.get("/module4/health")
async def module4_health():
    """Health check for Module4."""
    return {
        "status": "healthy",
        "module": "Module 4: Political Perspective Analysis Agents",
        "version": "1.0.0",
        "active_jobs": len(module4_jobs),
        "components": {
            "leftist_agent": True,
            "rightist_agent": True,
            "job_tracking": True
        }
    }

# ==================== DEBATE ENDPOINTS ====================

@app.post("/debate/start", response_model=DebateJobResponse)
async def start_debate(debate_request: DebateRequest, background_tasks: BackgroundTasks):
    """Start debate between leftist and rightist agents."""
    
    # Validate that both jobs exist and are completed
    if debate_request.leftist_job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Leftist job not found")
    
    if debate_request.rightist_job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Rightist job not found")
    
    leftist_job = module4_jobs[debate_request.leftist_job_id]
    rightist_job = module4_jobs[debate_request.rightist_job_id]
    
    if leftist_job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Leftist job not completed. Status: {leftist_job['status']}")
    
    if rightist_job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Rightist job not completed. Status: {rightist_job['status']}")
    
    if 'results' not in leftist_job or 'results' not in rightist_job:
        raise HTTPException(status_code=500, detail="Agent results not available for debate")
    
    # Create debate job
    job_id = f"debate_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    # Initialize job tracking
    module4_jobs[job_id] = {
        'job_id': job_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Debate job created',
        'started_at': time.time(),
        'agent_type': 'debate',
        'leftist_job_id': debate_request.leftist_job_id,
        'rightist_job_id': debate_request.rightist_job_id
    }
    
    # Start background task
    background_tasks.add_task(
        run_debate_task, 
        job_id, 
        leftist_job['results'], 
        rightist_job['results']
    )
    
    print(f"Started debate job: {job_id}")
    
    return DebateJobResponse(
        job_id=job_id,
        status="starting",
        message="Debate between agents started"
    )

@app.get("/debate/status/{job_id}")
async def get_debate_status(job_id: str):
    """Get debate job status."""
    if job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return module4_jobs[job_id]

@app.get("/debate/results/{job_id}")
async def get_debate_results(job_id: str):
    """Get debate results."""
    if job_id not in module4_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = module4_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")
    
    if 'results' not in job:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job['results']

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    import uvicorn
    print("Starting Module1, Module2, Module3 & Module4 Orchestrator...")
    print("Module1 URL Validator: http://localhost:8000/module1/validate")
    print("Module2 Misinformation Analyzer: http://localhost:8000/module2/analyze")
    print("Module3 Pipeline: http://localhost:8000/run")
    print("Module4 Leftist Agent: http://localhost:8000/leftist/start")
    print("Module4 Rightist Agent: http://localhost:8000/rightist/start")
    print("API Documentation: http://localhost:8000/docs")
    print("="*60)
    
    uvicorn.run(app, host="localhost", port=8000, reload=False)
