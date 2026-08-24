"""Evaluation CLI tool for FRONTLINE."""

import json
import logging
from pathlib import Path
from src.evaluation import Evaluator
from src.triage import TriagePipeline
from src.dataset import DatasetAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_dataset(dataset_path: str, ground_truth_path: str):
    """
    Evaluate predictions against ground truth.
    
    Usage:
        python cli_evaluate.py data/dataset.csv data/ground_truth.json
    """
    # Load dataset
    adapter = DatasetAdapter()
    messages, error = adapter.load(dataset_path)
    if error:
        logger.error(f"Failed to load dataset: {error}")
        return
    
    logger.info(f"Loaded {len(messages)} messages")
    
    # Process messages
    pipeline = TriagePipeline()
    results = pipeline.process_batch(messages)
    
    # Evaluate
    evaluator = Evaluator()
    count, error = evaluator.load_ground_truth(ground_truth_path)
    if error:
        logger.error(f"Failed to load ground truth: {error}")
        return
    
    logger.info(f"Loaded ground truth for {count} messages")
    metrics = evaluator.evaluate(results.results)
    
    # Report
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"Total messages evaluated: {metrics.total_messages}")
    print(f"Category agreement: {metrics.category_agreement:.1f}%")
    print(f"Priority agreement: {metrics.priority_agreement:.1f}%")
    print(f"Needs human agreement: {metrics.needs_human_agreement:.1f}%")
    print(f"Overall agreement: {metrics.overall_agreement:.1f}%")
    
    if metrics.failures:
        print(f"\nFirst {len(metrics.failures)} failures:")
        for failure in metrics.failures:
            print(f"  {failure['message_id']}: expected {failure['expected']}, got {failure['predicted']}")
    
    print("="*60)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python cli_evaluate.py <dataset> <ground_truth>")
        sys.exit(1)
    
    evaluate_dataset(sys.argv[1], sys.argv[2])
