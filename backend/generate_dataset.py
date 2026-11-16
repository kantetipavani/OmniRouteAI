"""
CLI Utility to generate Starter or Full synthetic datasets with fixed seed.
Supports:
  python generate_dataset.py --scale starter --seed 20261022
  python generate_dataset.py --scale full --seed 20261022
"""
import argparse
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.generator import SyntheticDataGenerator
from app.services.validator import data_validator

def main():
    parser = argparse.ArgumentParser(description="OmniRoute Synthetic Dataset Generator")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale: starter (1,000 tickets) or full (30,000 tickets)")
    parser.add_argument("--seed", type=int, default=20261022, help="Fixed random seed for deterministic generation")
    parser.add_argument("--output-dir", default="backend/data", help="Output directory for CSV, JSON and ground truth files")
    parser.add_argument("--verify", action="store_true", help="Run reproducibility and validation suite after generation")
    
    args = parser.parse_args()
    print(f"============================================================")
    print(f" Omniroute Synthetic Data Generator")
    print(f" Scale: {args.scale.upper()} | Seed: {args.seed} | Output: {args.output_dir}")
    print(f"============================================================")

    gen = SyntheticDataGenerator(seed=args.seed)
    print(f"[*] Generating master tables, lifecycle events, and edge cases...")
    data = gen.generate_all(scale=args.scale)
    
    print(f"[*] Exporting dataset to {args.output_dir}...")
    gen.export_to_disk(data, output_dir=args.output_dir)

    manifest = data["manifest"]
    print("\n[+] Dataset Generation Complete!")
    print(f"    - Customers:          {manifest['counts']['customers']}")
    print(f"    - Agents:             {manifest['counts']['agents']}")
    print(f"    - Tickets:            {manifest['counts']['tickets']}")
    print(f"    - Threaded Messages:  {manifest['counts']['messages']}")
    print(f"    - Assignment Events:  {manifest['counts']['assignment_events']}")
    print(f"    - SLA Events:         {manifest['counts']['sla_events']}")
    print(f"    - Resolutions:        {manifest['counts']['resolutions']}")
    print(f"    - Ground Truth Anoms: {manifest['counts']['ground_truth_anomalies']}")
    print(f"    - Dataset SHA-256:    {manifest['dataset_sha256']}")

    print("\n[+] Labeled Edge Cases Injected:")
    for k, v in manifest["anomalies_by_type"].items():
        print(f"    • {k:<25}: {v} anomalies")

    if args.verify:
        print("\n[*] Running Step 10 Reproducibility Verification...")
        rep = data_validator.verify_reproducibility(seed=args.seed)
        print(f"    - Bitwise Checksum Match: {rep['reproducible']}")
        print(f"    - Run 1 Checksum:         {rep['run_1_checksum']}")
        print(f"    - Run 2 Checksum:         {rep['run_2_checksum']}")

if __name__ == "__main__":
    main()
