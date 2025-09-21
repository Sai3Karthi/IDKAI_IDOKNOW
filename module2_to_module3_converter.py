#!/usr/bin/env python3
"""
Module2 to Module3 Format Converter
===================================

This utility converts Module2 output format to Module3 input format and 
automatically updates the input.json file in Module3.

Module2 Output Format:
{
  "classification": {...},
  "significance_score": int (0-100),
  "summary": "text",
  "source": bool
}

Module3 Input Format:
{
  "topic": "short title",
  "text": "summary text", 
  "significance_score": float (0-1)
}
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

# Define paths
BASE_DIR = Path(__file__).resolve().parent
MODULE3_INPUT_PATH = BASE_DIR / "module3" / "backend" / "input.json"

def convert_module2_to_module3_format(module2_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Module2 output format to Module3 input format.
    
    Args:
        module2_data: Dictionary containing Module2 output
        
    Returns:
        dict: Formatted data for Module3 input.json
    """
    # Extract summary text
    summary_text = module2_data.get("summary", "")
    
    # Generate a topic based on the summary content
    if summary_text:
        # Take first meaningful part of the summary for topic
        topic_words = summary_text.split()[:12]  # Take first 12 words
        topic = " ".join(topic_words)
        
        # Clean up and limit topic length
        if len(topic) > 80:
            topic = topic[:77] + "..."
        
        # Remove trailing punctuation if present
        topic = topic.rstrip('.,!?;:')
    else:
        topic = "Analysis Result"
    
    # Convert significance score from integer (0-100) to float (0-1)
    significance_score = module2_data.get("significance_score", 0)
    significance_score_normalized = significance_score / 100.0
    
    # Ensure score is within 0-1 range
    significance_score_normalized = max(0.0, min(1.0, significance_score_normalized))
    
    return {
        "topic": topic,
        "text": summary_text,
        "significance_score": significance_score_normalized
    }

def update_module3_input_json(formatted_data: Dict[str, Any]) -> bool:
    """
    Update Module3's input.json file with formatted data.
    
    Args:
        formatted_data: Dictionary containing topic, text, and significance_score
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure the directory exists
        MODULE3_INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the formatted data to input.json
        with open(MODULE3_INPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Updated Module3 input.json successfully")
        print(f"  Topic: '{formatted_data['topic']}'")
        print(f"  Significance Score: {formatted_data['significance_score']}")
        return True
        
    except Exception as e:
        print(f"✗ Error updating Module3 input.json: {str(e)}")
        return False

def convert_and_update(module2_output: Dict[str, Any]) -> bool:
    """
    Convert Module2 output and update Module3 input.json in one step.
    
    Args:
        module2_output: Dictionary containing Module2 output
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("Converting Module2 output to Module3 format...")
    
    # Convert format
    formatted_data = convert_module2_to_module3_format(module2_output)
    
    # Update input.json
    success = update_module3_input_json(formatted_data)
    
    if success:
        print("✓ Conversion and update completed successfully")
    else:
        print("✗ Conversion failed")
    
    return success

def main():
    """Main function for command line usage."""
    # Example usage with the provided Module2 output
    example_module2_output = {
        "classification": {
            "person": 95,
            "organization": 0,
            "social": 5,
            "critical": 0,
            "stem": 0
        },
        "significance_score": 25,
        "summary": "The provided statement expresses an opinion or belief that an individual named Abdullah is gay. It is important to recognize that this is an assertion about Abdullah's sexual orientation, and without further information or confirmation from Abdullah himself, it remains an unverified claim. Sexual orientation is a personal and private aspect of an individual's identity, and assumptions or declarations about it should be treated with sensitivity and respect for individual autonomy.",
        "source": False
    }
    
    print("Module2 to Module3 Format Converter")
    print("=" * 40)
    
    # Convert and update
    convert_and_update(example_module2_output)

if __name__ == "__main__":
    main()