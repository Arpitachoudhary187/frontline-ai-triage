"""Tests for batch processing robustness."""

import pytest
from src.models import BatchResults


def test_batch_results_schema():
    """Test BatchResults model validation."""
    batch = BatchResults(
        total_messages=10,
        successful_classifications=9,
        failed_classifications=1,
        escalated_to_human=2,
        average_confidence=0.82,
        average_latency_ms=245.5,
        priority_distribution={"P0": 1, "P1": 3, "P2": 5, "P3": 1},
        results=[]
    )
    
    assert batch.total_messages == 10
    assert batch.successful_classifications == 9
    assert batch.failed_classifications == 1


def test_single_message_batch():
    """Test batch with single message."""
    batch = BatchResults(
        total_messages=1,
        successful_classifications=1,
        failed_classifications=0,
        escalated_to_human=0,
        average_confidence=0.95,
        average_latency_ms=150.0,
        priority_distribution={"P0": 0, "P1": 0, "P2": 1, "P3": 0},
        results=[]
    )
    
    assert batch.total_messages == 1


def test_all_failures_batch():
    """Test batch where all messages fail."""
    batch = BatchResults(
        total_messages=5,
        successful_classifications=0,
        failed_classifications=5,
        escalated_to_human=5,
        average_confidence=0.0,
        average_latency_ms=100.0,
        priority_distribution={"P0": 0, "P1": 0, "P2": 5, "P3": 0},
        results=[]
    )
    
    assert batch.successful_classifications == 0
    assert batch.failed_classifications == 5
