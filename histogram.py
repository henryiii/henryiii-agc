import argparse
from pathlib import Path

import awkward as ak
import hist
import uproot

from file_input import construct_fileset

STEP_SIZE = 500_000


def jet_pt_histogram(files: list[str]) -> hist.Hist:
    h = hist.Hist.new.Reg(50, 0, 300, name="jet_pt", label="Jet $p_T$ [GeV]").Double()
    # A memory-size step_size reads every basket key one at a time, which is
    # very slow over high-latency remote access (scikit-hep/uproot5#1797).
    for arrays in uproot.iterate(
        {f: "Events" for f in files}, ["Jet_pt"], step_size=STEP_SIZE
    ):
        h.fill(jet_pt=ak.flatten(arrays["Jet_pt"]))
    return h


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill histograms for one sample")
    parser.add_argument("sample", help="Fileset key, like ttbar__nominal")
    parser.add_argument("output", type=Path, help="Output ROOT file")
    parser.add_argument("--n-files", type=int, default=-1)
    args = parser.parse_args()

    files = construct_fileset(args.n_files)[args.sample]["files"]
    h = jet_pt_histogram(files)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with uproot.recreate(args.output) as f:
        f["jet_pt"] = h


if __name__ == "__main__":
    main()
