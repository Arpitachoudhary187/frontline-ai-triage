"""
Dataset adapter for FRONTLINE triage.

Supports CSV and JSON formats.
Auto-detects message column and provides stable message IDs.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import uuid

logger = logging.getLogger(__name__)


class DatasetAdapter:
    """
    Flexible dataset loader supporting CSV and JSON formats.
    Auto-detects message column if not specified.
    Provides stable message IDs.
    """

    # Common column names for customer messages
    MESSAGE_COLUMN_ALIASES = [
        "message", "text", "content", "customer_message",
        "message_text", "body", "description", "issue",
        "subject", "query", "msg", "input"
    ]

    def __init__(self):
        """Initialize dataset adapter."""
        self.messages = []

    def load(self, filepath: str, message_column: Optional[str] = None) -> Tuple[List[dict], Optional[str]]:
        """
        Load dataset from CSV or JSON.
        
        Args:
            filepath: Path to dataset file
            message_column: Specific column name (auto-detects if not provided)
        
        Returns:
            (messages: List[dict], error: Optional[str])
            Each message dict has: id, text
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return [], f"File not found: {filepath}"

            if path.suffix.lower() == ".csv":
                return self._load_csv(filepath, message_column)
            elif path.suffix.lower() == ".json":
                return self._load_json(filepath, message_column)
            else:
                return [], f"Unsupported format: {path.suffix}. Use CSV or JSON."

        except Exception as e:
            logger.error(f"Dataset load error: {str(e)}")
            return [], str(e)

    def _load_csv(self, filepath: str, message_column: Optional[str] = None) -> Tuple[List[dict], Optional[str]]:
        """Load CSV dataset."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                return [], "CSV file is empty"

            # Auto-detect message column
            col = message_column or self._detect_message_column(rows[0].keys())
            if not col:
                return [], "Could not detect message column"

            messages = []
            for idx, row in enumerate(rows):
                text = row.get(col, "").strip()
                if text:
                    messages.append({
                        "id": f"csv_{idx:06d}",
                        "text": text
                    })

            logger.info(f"Loaded {len(messages)} messages from CSV")
            return messages, None

        except Exception as e:
            return [], f"CSV load error: {str(e)}"

    def _load_json(self, filepath: str, message_column: Optional[str] = None) -> Tuple[List[dict], Optional[str]]:
        """Load JSON dataset."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both list of objects and single object
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                rows = [data]
            else:
                return [], "JSON must be a list or object"

            if not rows:
                return [], "JSON dataset is empty"

            # Auto-detect message column
            col = message_column or self._detect_message_column(rows[0].keys())
            if not col:
                return [], "Could not detect message column"

            messages = []
            for idx, row in enumerate(rows):
                text = row.get(col, "").strip()
                if text:
                    messages.append({
                        "id": f"json_{idx:06d}",
                        "text": text
                    })

            logger.info(f"Loaded {len(messages)} messages from JSON")
            return messages, None

        except Exception as e:
            return [], f"JSON load error: {str(e)}"

    def _detect_message_column(self, columns) -> Optional[str]:
        """Auto-detect message column from header."""
        columns_lower = {col.lower(): col for col in columns}
        
        for alias in self.MESSAGE_COLUMN_ALIASES:
            if alias in columns_lower:
                detected = columns_lower[alias]
                logger.info(f"Auto-detected message column: {detected}")
                return detected

        # Fall back to first column if nothing matches
        if columns:
            logger.warning(f"No message column detected. Using first column: {columns[0]}")
            return columns[0]

        return None
