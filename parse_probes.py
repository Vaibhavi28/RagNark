import json
import os

# --- CONFIGURE THESE TWO LINES ---
INPUT_FILE = "pass1_output.txt"   # the file you saved in Step 3
OUTPUT_DIR = "probes"             # your probes folder
# ----------------------------------

CATEGORY_FOLDERS = {
    "exfiltration": "exfiltration",
    "access_control": "access_control",
    "prompt_injection": "prompt_injection",
    "indirect_injection": "indirect_injection",
    "multi_turn": "multi_turn"
}

# Read the output file
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = f.read()

# Split into individual probe blocks
blocks = raw.split("---FILE_END---")

success = 0
skipped = 0
errors = []

for i, block in enumerate(blocks):
    block = block.strip()

    # Skip empty blocks and checkpoints
    if not block:
        continue
    if "CHECKPOINT" in block:
        continue
    if "CONFIRMED:" in block:
        continue

    # Try to parse as JSON
    try:
        probe = json.loads(block)
    except json.JSONDecodeError as e:
        errors.append(f"Block {i+1}: Invalid JSON — {e}")
        skipped += 1
        continue

    # Check required fields exist
    if "id" not in probe or "category" not in probe:
        errors.append(f"Block {i+1}: Missing id or category field")
        skipped += 1
        continue

    # Get the folder for this category
    category = probe["category"]
    if category not in CATEGORY_FOLDERS:
        errors.append(f"Block {i+1}: Unknown category '{category}'")
        skipped += 1
        continue

    # Create the folder if it does not exist
    folder = os.path.join(OUTPUT_DIR, CATEGORY_FOLDERS[category])
    os.makedirs(folder, exist_ok=True)

    # Write the file
    filename = f"{probe['id']}.json"
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(probe, f, indent=2)

    success += 1
    print(f"Saved: {filepath}")

# Print summary
print(f"\n--- DONE ---")
print(f"Saved:   {success} probes")
print(f"Skipped: {skipped} blocks")
if errors:
    print(f"\nErrors:")
    for e in errors:
        print(f"  {e}")