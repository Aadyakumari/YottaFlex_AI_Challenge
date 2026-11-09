import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run(script, *args):
    print(f"\n--- Running {script} ---", flush=True)
    subprocess.run(
        [sys.executable, str(ROOT / "src" / script), *args],
        cwd=ROOT,
        check=True
    )

def main():
    parser = argparse.ArgumentParser(description="Student Fee Management System")
    parser.add_argument("--scale", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()

    run("database.py")
    run("data_generator.py", "--scale", str(args.scale), "--seed", str(args.seed))
    run("validators.py")
    run("export_data.py")

    print("\nPipeline completed successfully.")

if __name__ == "__main__":
    main()
