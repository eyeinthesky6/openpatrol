from __future__ import annotations
import argparse,json
from pathlib import Path
from .virtual_hardware import run_acceptance

def main() -> None:
    parser=argparse.ArgumentParser(description="Run the deterministic OpenPatrol virtual-hardware acceptance suite")
    parser.add_argument("--output",type=Path); args=parser.parse_args(); report=run_acceptance(args.output)
    print(json.dumps(report,indent=2)); raise SystemExit(0 if report["result"]=="pass" else 1)

if __name__=="__main__": main()
