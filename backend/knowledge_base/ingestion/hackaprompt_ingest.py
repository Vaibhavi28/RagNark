import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset
from datasets.exceptions import DatasetNotFoundError
from huggingface_hub import HfApi, dataset_info
from huggingface_hub.utils import HfHubHTTPError
import requests

DATASET_ID = "hackaprompt/hackaprompt-dataset"
SOURCE_URL = f"https://huggingface.co/datasets/{DATASET_ID}"
UNKNOWN_LICENSE = "UNKNOWN — MANUAL REVIEW REQUIRED"

DEFAULT_SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = DEFAULT_SCRIPT_DIR.parent.parent.parent
DEFAULT_RAW_DATA_DIR = DEFAULT_BASE_DIR / "backend" / "knowledge_base" / "raw_data" / "hackaprompt"
DEFAULT_CHECKPOINT_PATH = DEFAULT_SCRIPT_DIR / "ingestion_checkpoint.json"

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(DEFAULT_BASE_DIR / ".env")
except ImportError:
    pass



def get_dataset_license_and_revision(dataset_id=DATASET_ID, token=None):
    """Fetch license metadata and commit sha from HuggingFace dataset card."""
    try:
        info = dataset_info(dataset_id, token=token)
        revision_hash = getattr(info, "sha", None)
        card_data = getattr(info, "card_data", None)

        license_val = None
        if card_data is not None:
            if hasattr(card_data, "get"):
                license_val = card_data.get("license")
            if not license_val and hasattr(card_data, "license"):
                license_val = card_data.license

        if not license_val:
            license_val = UNKNOWN_LICENSE

        return license_val, revision_hash
    except HfHubHTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            print(f"Error: HuggingFace dataset '{dataset_id}' not found or renamed.")
            sys.exit(1)
        raise
    except (requests.exceptions.ConnectionError, socket.gaierror) as e:
        print(f"Error: No internet connection or HuggingFace Hub is unreachable: {e}")
        sys.exit(1)


def load_dataset_with_retries(dataset_id=DATASET_ID, token=None, max_retries=3, delay_seconds=5):
    """Load dataset from HuggingFace with timeout retries and specific error handling."""
    for attempt in range(1, max_retries + 1):
        try:
            dataset = load_dataset(dataset_id, token=token)
            return dataset
        except (requests.exceptions.Timeout, TimeoutError, socket.timeout) as e:
            if attempt < max_retries:
                print(f"Network timeout on attempt {attempt}/{max_retries}. Retrying in {delay_seconds} seconds...")
                time.sleep(delay_seconds)
            else:
                print(f"Error: Network timed out after {max_retries} attempts.")
                sys.exit(1)
        except (requests.exceptions.ConnectionError, socket.gaierror) as e:
            print(f"Error: No internet connection or HuggingFace Hub is unreachable: {e}")
            sys.exit(1)
        except DatasetNotFoundError as e:
            err_msg = str(e)
            if "gated" in err_msg.lower() or "authenticated" in err_msg.lower() or "ask for access" in err_msg.lower():
                print(
                    f"Error: Dataset '{dataset_id}' is a gated dataset on the Hub.\n"
                    f"Please visit: https://huggingface.co/datasets/{dataset_id}\n"
                    "Log in to your HuggingFace account and click 'Agree and access repository' / 'Acknowledge' to grant access to your account."
                )
            else:
                print(f"Error: HuggingFace dataset '{dataset_id}' not found or renamed.")
            sys.exit(1)
        except HfHubHTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                print(f"Error: HuggingFace dataset '{dataset_id}' not found or renamed.")
                sys.exit(1)
            raise


def ingest_hackaprompt(raw_data_dir=None, checkpoint_path=None, dataset_id=DATASET_ID, token=None):
    """Run the raw ingestion process for HackAPrompt."""
    raw_data_dir = Path(raw_data_dir) if raw_data_dir else DEFAULT_RAW_DATA_DIR
    checkpoint_path = Path(checkpoint_path) if checkpoint_path else DEFAULT_CHECKPOINT_PATH

    raw_dump_path = raw_data_dir / "raw_dump.jsonl"
    provenance_path = raw_data_dir / "provenance.json"

    # Step 2: Checkpoint verification
    checkpoint = {
        "sources_completed": [],
        "hackaprompt_rows_downloaded": 0,
        "last_run_timestamp": None
    }
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
        except Exception:
            pass

    if "hackaprompt" in checkpoint.get("sources_completed", []):
        print("HackAPrompt already ingested — skipping. Delete checkpoint entry to force re-run.")
        return {
            "status": "skipped",
            "reason": "already_ingested",
            "num_rows_ingested": checkpoint.get("hackaprompt_rows_downloaded", 0)
        }

    # Resolve token if not provided
    if token is None:
        token = os.environ.get("HF_TOKEN")
    if token:
        token = token.strip()

    print(f"Starting ingestion for dataset: {dataset_id}")

    # Step 1.2: License metadata & commit sha
    license_detected, dataset_revision_hash = get_dataset_license_and_revision(dataset_id=dataset_id, token=token)
    print(f"License detected: {license_detected}")
    if dataset_revision_hash:
        print(f"Dataset revision: {dataset_revision_hash}")

    # Step 1.1 & Step 3: Pull dataset with error handling
    dataset = load_dataset_with_retries(dataset_id=dataset_id, token=token)

    # Step 1.3: Save RAW, unmodified rows to JSONL
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    num_rows_ingested = 0

    with open(raw_dump_path, "w", encoding="utf-8") as f:
        if hasattr(dataset, "keys"):
            for split_name in dataset.keys():
                split_data = dataset[split_name]
                for row in split_data:
                    f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
                    num_rows_ingested += 1
        else:
            for row in dataset:
                f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
                num_rows_ingested += 1

    print(f"Saved {num_rows_ingested} raw rows to {raw_dump_path}")

    # Step 1.4: Provenance file
    ingestion_date = datetime.now(timezone.utc).isoformat()
    provenance = {
        "source_name": "HackAPrompt",
        "source_url": SOURCE_URL,
        "license_detected": license_detected,
        "num_rows_ingested": num_rows_ingested,
        "ingestion_date": ingestion_date,
        "dataset_revision_hash": dataset_revision_hash,
        "review_status": "NEEDS_MANUAL_REVIEW"
    }

    with open(provenance_path, "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2)
    print(f"Saved provenance to {provenance_path}")

    # Step 2: Update checkpoint
    if "hackaprompt" not in checkpoint.get("sources_completed", []):
        checkpoint.setdefault("sources_completed", []).append("hackaprompt")
    checkpoint["hackaprompt_rows_downloaded"] = num_rows_ingested
    checkpoint["last_run_timestamp"] = ingestion_date

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    print(f"Updated checkpoint at {checkpoint_path}")

    return {
        "status": "success",
        "provenance": provenance,
        "num_rows_ingested": num_rows_ingested
    }


if __name__ == "__main__":
    ingest_hackaprompt()
