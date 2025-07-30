"""
JSON Extraction Utilities

This module provides functions for extracting JSON objects from text responses
that may contain JSON embedded within markdown or other formatting.

Functions:
    extract_json_from_text: Extract JSON from free-text with multiple parsing strategies
"""

import json
import re
from typing import Dict, Any


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from free-text that may contain JSON embedded within it.
    
    Uses multiple parsing strategies to handle various formats:
    1. Direct JSON parsing
    2. Code fence extraction (```json ... ```)
    3. Trigger phrase patterns (CRITICAL:, JSON object:, etc.)
    4. Nested brace matching
    5. Simple brace pattern matching
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Extracted JSON dictionary or empty dict if no valid JSON found
    """
    # First try to parse the entire text as JSON
    try:
        return json.loads(text.strip())
    except:
        pass
    
    # Look for JSON blocks within code fences
    # Pattern 1: ```json ... ```
    json_blocks = re.findall(r'```json\s*\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
    for block in json_blocks:
        try:
            return json.loads(block.strip())
        except:
            continue
    
    # Pattern 2: ``` ... ``` (without language specifier)
    code_blocks = re.findall(r'```\s*\n(.*?)\n```', text, re.DOTALL)
    for block in code_blocks:
        try:
            return json.loads(block.strip())
        except:
            continue
    
    # Pattern 3: Look for JSON after "CRITICAL:" or specific trigger phrases
    critical_json_patterns = [
        r'CRITICAL:.*?(\{.*\})',
        r'JSON object.*?(\{.*\})',
        r'format.*?findings.*?(\{.*\})',
        r'structure.*?(\{.*\})',
    ]
    
    for pattern in critical_json_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                # Clean escaped characters that might break JSON parsing
                cleaned_match = match.replace('\\"', '"').replace('\\!', '!')
                return json.loads(cleaned_match)
            except:
                # Try original if cleaning didn't work
                try:
                    return json.loads(match)
                except:
                    continue
    
    # Pattern 4: Look for complete JSON objects with nested braces (improved)
    # Find all potential JSON start positions
    potential_starts = []
    for i, char in enumerate(text):
        if char == '{':
            potential_starts.append(i)
    
    # Try each potential start position
    for start_idx in potential_starts:
        brace_count = 0
        for i in range(start_idx, len(text)):
            char = text[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found a complete JSON object
                    candidate = text[start_idx:i+1]
                    try:
                        parsed = json.loads(candidate)
                        # Additional validation: must have expected fields
                        if isinstance(parsed, dict) and ('index' in parsed or 'title' in parsed):
                            return parsed
                    except:
                        continue
                    break
    
    # Pattern 5: Look for { ... } blocks (simple patterns) 
    brace_matches = re.findall(r'\{[^{}]*\}', text, re.DOTALL)
    for match in brace_matches:
        try:
            parsed = json.loads(match)
            if isinstance(parsed, dict) and ('index' in parsed or 'title' in parsed):
                return parsed
        except:
            continue
    
    # Debug: Print what we couldn't parse (first 200 chars)
    print(f"    🔍 Could not extract JSON from text (first 200 chars): {text[:200]}...")
    
    return {}