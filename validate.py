import argparse
import json
import sys
from pathlib import Path

import numpy as np
import uproot


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare histograms with an AGC reference file"
    )
    parser.add_argument("histograms", type=Path, help="Merged ROOT file")
    parser.add_argument("reference", type=Path, help="AGC reference JSON file")
    args = parser.parse_args()

    reference = json.loads(args.reference.read_text())

    failed = False
    with uproot.open(args.histograms) as f:
        names = f.keys(cycle=False)
        for name in sorted(names):
            if name not in reference:
                print(f"{name}: not in reference")
                failed = True
                continue
            h = f[name]
            edges = h.axis().edges()
            contents = h.counts(flow=True)
            ref = reference[name]
            if not np.allclose(edges, ref["edges"]):
                print(f"{name}: edges do not match")
                failed = True
            elif not np.allclose(contents, ref["contents"]):
                diff = np.abs(contents - ref["contents"]).max()
                print(f"{name}: contents do not match (max diff {diff:.4g})")
                failed = True
            else:
                print(f"{name}: OK")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
