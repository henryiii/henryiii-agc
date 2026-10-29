import argparse
from pathlib import Path

import uproot

from histogram import REGIONS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge per-sample histograms and add pseudodata"
    )
    parser.add_argument("output", type=Path, help="Output ROOT file")
    parser.add_argument("inputs", type=Path, nargs="+", help="Per-sample ROOT files")
    args = parser.parse_args()

    hists = {}
    for path in args.inputs:
        with uproot.open(path) as f:
            hists.update({k: f[k].to_hist() for k in f.keys(cycle=False)})

    for region in REGIONS:
        parts = [f"{region}_ttbar_ME_var", f"{region}_ttbar_PS_var", f"{region}_wjets"]
        if all(p in hists for p in parts):
            me, ps, wjets = (hists[p] for p in parts)
            hists[f"{region}_pseudodata"] = (me + ps) / 2 + wjets

    with uproot.recreate(args.output) as f:
        for name, h in hists.items():
            f[name] = h


if __name__ == "__main__":
    main()
