"""
LLM client wrapper for FRONTLINE triage.

Handles communication with Claude API, structured output parsing, and retry logic.
"""

import json
import os
import time
import logging
from typing import Optional, Tuple
from src.models import TriageDecision
from src.prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False
    logger.warning("Claude SDK not installed. Install with: pip install anthropic")


class LLMClient:
    """
    Claude API wrapper for triage classification.
    Handles structured output parsing and retry logic.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize LLM client.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        if not HAS_CLAUDE:
            raise ImportError("Claude SDK required: pip install anthropic")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT
        self.token_usage = {"input": 0, "output": 0}

    def classify(self, message: str, max_retries: int = 2) -> Tuple[Optional[TriageDecision], Optional[str]]:
        """
        Classify a single customer message.
        
        Args:
            message: Raw customer message
            max_retries: Number of retry attempts for malformed output
        
        Returns:
            (TriageDecision, error_message) - One will be None
        """
        if not message or not message.strip():
            logger.warning("Empty message received")
            return None, "Empty message"

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    system=self.system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": message
                        }
                    ]
                )

                # Track token usage
                self.token_usage["input"] += response.usage.input_tokens
                self.token_usage["output"] += response.usage.output_tokens

                # Extract response text
                response_text = response.content[0].text.strip()

                # Parse JSON
                decision = self._parse_json_response(response_text)
                if decision:
                    return decision, None
                else:
                    error_msg = f"Failed to parse JSON after attempt {attempt + 1}"
                    logger.warning(f"{error_msg}: {response_text[:100]}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(0.5)  # Brief delay before retry
                        continue
                    else:
                        return None, error_msg

            except json.JSONDecodeError as e:
                error_msg = f"JSON decode error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1}: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                return None, error_msg

            except Exception as e:
                error_msg = f"LLM API error: {str(e)}"
                logger.error(error_msg)
                return None, error_msg

        return None, "Max retries exceeded"

    def _parse_json_response(self, response_text: str) -> Optional[TriageDecision]:
        """
        Parse and validate JSON response from LLM.
        Attempts to extract JSON from markdown code blocks if needed.
        
        Args:
            response_text: Raw response from LLM
        
        Returns:
            TriageDecision if valid, None otherwise
        """
        try:
            # Try direct parse
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract from markdown code block
            if "```json" in response_text:
                try:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    if end > start:
                        json_str = response_text[start:end].strip()
                        data = json.loads(json_str)
                    else:
                        return None
                except (json.JSONDecodeError, ValueError):
                    return None
            else:
                return None

        # Validate against Pydantic model
        try:
            decision = TriageDecision(**data)
            return decision
        except Exception as e:
            logger.warning(f"Pydantic validation error: {str(e)}")
            return None

    def get_token_summary(self) -> dict:
        """Return token usage summary."""
        return {
            "input_tokens": self.token_usage["input"],
            "output_tokens": self.token_usage["output"],
            "total_tokens": self.token_usage["input"] + self.token_usage["output"]
        }
