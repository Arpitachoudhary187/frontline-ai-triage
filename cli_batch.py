"""Batch processing CLI tool for FRONTLINE."""

import json
import logging
from pathlib import Path
from datetime import datetime
from src.triage import TriagePipeline
from src.dataset import DatasetAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_dataset(dataset_path: str, output_path: str = None):
    """
    Process entire dataset and save results.
    
    Usage:
        python cli_batch.py data/messages.csv output/results.json
    """
    # Load dataset
    adapter = DatasetAdapter()
    messages, error = adapter.load(dataset_path)
    if error:
        logger.error(f"Failed to load dataset: {error}")
        return
    
    logger.info(f"Loaded {len(messages)} messages")
    
    # Process
    pipeline = TriagePipeline()
    results = pipeline.process_batch(messages)
    
    # Report summary
    print("\n" + "="*60)
    print("BATCH PROCESSING COMPLETE")
    print("="*60)
    print(f"Total messages: {results.total_messages}")
    print(f"Successful: {results.successful_classifications}")
    print(f"Failed: {results.failed_classifications}")
    print(f"Escalated to human: {results.escalated_to_human}")
    print(f"Average confidence: {results.average_confidence:.2f}")
    print(f"Average latency: {results.average_latency_ms:.1f}ms")
    print(f"\nPriority distribution:")
    for priority, count in results.priority_distribution.items():
        print(f"  {priority}: {count}")
    print("="*60)
    
    # Save results
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_messages": results.total_messages,
                "successful": results.successful_classifications,
                "failed": results.failed_classifications,
                "escalated": results.escalated_to_human,
                "avg_confidence": results.average_confidence,
                "avg_latency_ms": results.average_latency_ms,
                "priority_distribution": results.priority_distribution
            },
            "results": [
                {
                    "message_id": r.message_id,
                    "message_text": r.message_text[:100],
                    "decision": r.decision.dict(),
                    "latency_ms": r.latency_ms,
                    "validation_error": r.validation_error,
                    "escalation_reason": r.escalation_reason
                }
                for r in results.results
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_file}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python cli_batch.py <dataset> [output_file]")
        sys.exit(1)
    
    output = sys.argv[2] if len(sys.argv) > 2 else "output/results.json"
    process_dataset(sys.argv[1], output)
