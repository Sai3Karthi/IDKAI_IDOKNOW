"""
Debate Agent - Facilitates structured debates between leftist and rightist agents
with a points-based scoring system to determine information credibility.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebateAgent:
    """Facilitates structured debates between political perspective agents."""
    
    def __init__(self):
        """Initialize the debate agent."""
        self.gemini_key = os.getenv("GENAI_API_KEY")
        if not self.gemini_key:
            raise ValueError("GENAI_API_KEY environment variable is required")
        
        # Initialize Gemini AI for debate moderation
        genai.configure(api_key=self.gemini_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
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
        
        logger.info("Debate Agent initialized")
    
    async def conduct_debate(self, leftist_results: Dict, rightist_results: Dict) -> Dict:
        """
        Conduct a structured debate between leftist and rightist research results.
        
        Args:
            leftist_results: Research results from leftist agent
            rightist_results: Research results from rightist agent
            
        Returns:
            Dict containing debate results, scores, and winner determination
        """
        logger.info("🎯 Starting structured debate between agents")
        
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
        
        logger.info(f"   📊 Leftist claims: {len(leftist_claims)}")
        logger.info(f"   📊 Rightist claims: {len(rightist_claims)}")
        
        # Conduct debate rounds
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"\n🔥 DEBATE ROUND {round_num}")
            logger.info("=" * 50)
            
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
            if round_result["round_winner"]:
                debate_session["scores"][round_result["round_winner"]] += round_result["points_awarded"]
                
                logger.info(f"   🏆 Round {round_num} winner: {round_result['round_winner'].upper()}")
                logger.info(f"   📈 Current scores - Leftist: {debate_session['scores']['leftist']}, Rightist: {debate_session['scores']['rightist']}")
            
            # Check for early victory
            if (debate_session["scores"]["leftist"] >= self.points_to_win or 
                debate_session["scores"]["rightist"] >= self.points_to_win):
                logger.info(f"\n🎯 Early victory achieved after {round_num} rounds!")
                break
            
            # Brief pause between rounds
            await asyncio.sleep(1)
        
        # Determine final winner
        debate_session["winner"] = self._determine_final_winner(debate_session["scores"])
        debate_session["duration"] = time.time() - debate_session["start_time"]
        
        # Generate debate summary
        debate_session["debate_summary"] = await self._generate_debate_summary(debate_session)
        
        logger.info(f"\n🏁 DEBATE CONCLUDED")
        logger.info(f"   ⏱️  Duration: {debate_session['duration']:.1f}s")
        logger.info(f"   🏆 Winner: {debate_session['winner'].upper() if debate_session['winner'] else 'TIE'}")
        logger.info(f"   📊 Final scores - Leftist: {debate_session['scores']['leftist']}, Rightist: {debate_session['scores']['rightist']}")
        
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
            logger.error(f"Error in round {round_num}: {e}")
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
            logger.error(f"Error generating argument: {e}")
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
            logger.error(f"Error generating counter-argument: {e}")
            return f"However, our analysis of {len(claim_data.get('sources', []))} sources reveals {claim_data.get('claim', 'a different perspective')}."
    
    async def _evaluate_round(self, round_data: Dict, first_claims: List, second_claims: List) -> tuple:
        """Evaluate round winner based on argument quality."""
        
        evaluation_context = f"""Evaluate this debate round objectively:

First Speaker ({round_data['first_speaker']}): {round_data['first_argument']}
Second Speaker ({round_data['second_speaker']}): {round_data['second_argument']}

Scoring Criteria:
- Evidence Quality (0-2 points): Factual, verifiable information
- Source Credibility (0-2 points): Authoritative, reliable sources  
- Logical Consistency (0-1 points): Internal logic and coherence
- Response Relevance (0-1 points): Addresses opponent's points directly

Total possible: 6 points per argument.

Evaluate both arguments and determine:
1. Who presented stronger evidence?
2. Who had more credible sources?
3. Who was more logically consistent?
4. Who better addressed the debate topic?

Return only: "first" or "second" or "tie", followed by points (1-2), followed by brief reasoning."""

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, evaluation_context
            )
            
            evaluation = response.text.strip().lower()
            
            # Parse evaluation
            if "first" in evaluation and "tie" not in evaluation:
                winner = round_data['first_speaker']
                points = 2 if "strong" in evaluation or "clear" in evaluation else 1
            elif "second" in evaluation and "tie" not in evaluation:
                winner = round_data['second_speaker']
                points = 2 if "strong" in evaluation or "clear" in evaluation else 1
            else:
                winner = None
                points = 0
            
            reasoning = evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating round: {e}")
            # Fallback: simple length-based evaluation
            first_len = len(round_data.get('first_argument', ''))
            second_len = len(round_data.get('second_argument', ''))
            
            if first_len > second_len + 20:
                winner = round_data['first_speaker']
                points = 1
                reasoning = "Awarded based on argument detail and evidence presentation."
            elif second_len > first_len + 20:
                winner = round_data['second_speaker'] 
                points = 1
                reasoning = "Awarded based on argument detail and evidence presentation."
            else:
                winner = None
                points = 0
                reasoning = "Round tie - both arguments equally matched."
        
        return winner, points, reasoning
    
    def _determine_final_winner(self, scores: Dict) -> Optional[str]:
        """Determine the final debate winner."""
        if scores["leftist"] > scores["rightist"]:
            return "leftist"
        elif scores["rightist"] > scores["leftist"]:
            return "rightist"
        else:
            return None  # Tie
    
    async def _generate_debate_summary(self, debate_session: Dict) -> str:
        """Generate a comprehensive debate summary."""
        
        summary_context = f"""Summarize this political debate session:

Total Rounds: {debate_session['total_rounds']}
Final Scores: Leftist {debate_session['scores']['leftist']} - Rightist {debate_session['scores']['rightist']}
Winner: {debate_session['winner'] or 'Tie'}
Duration: {debate_session.get('duration', 0):.1f} seconds

Generate a professional 3-4 sentence summary covering:
1. Key arguments presented by both sides
2. Quality of evidence and sources
3. Why the winner prevailed (or why it was a tie)
4. Overall assessment of information credibility

Keep it objective and analytical."""

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, summary_context
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            winner_text = f"The {debate_session['winner']} perspective" if debate_session['winner'] else "Both perspectives"
            return f"{winner_text} demonstrated stronger evidence in this {debate_session['total_rounds']}-round debate, with final scores of {debate_session['scores']['leftist']}-{debate_session['scores']['rightist']}."