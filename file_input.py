import argparse
import json
from pathlib import Path

PELICAN_PREFIX = "pelican://osg-htc.org/cern-opendata/upload/agc/1.0.0"
UNL_PREFIX = "https://xrootd-local.unl.edu:1094//store/user/AGC/nanoAOD"

INPUTS = Path(__file__).parent / "nanoaod_inputs.json"

# x-secs are in pb
XSEC_INFO = {
    "ttbar": 396.87 + 332.97,  # nonallhad + allhad, keep same x-sec for all
    "single_top_s_chan": 2.0268 + 1.2676,
    # scale from lepton filter to inclusive
    "single_top_t_chan": (36.993 + 22.175) / 0.252,
    "single_top_tW": 37.936 + 37.906,
    "wjets": 61457 * 0.252,  # e/mu+nu final states
}


def construct_fileset(n_files_max_per_sample: int = -1) -> dict[str, dict]:
    """
    Build a fileset with pelican:// URLs to the CERN open data copy of the AGC
    inputs. Use ``n_files_max_per_sample=-1`` for all files.
    """
    with INPUTS.open() as f:
        file_info = json.load(f)

    fileset = {}
    for process, variations in file_info.items():
        if process == "data":
            continue

        for variation, info in variations.items():
            file_list = info["files"]
            if n_files_max_per_sample != -1:
                file_list = file_list[:n_files_max_per_sample]

            files = [f["path"].replace(UNL_PREFIX, PELICAN_PREFIX) for f in file_list]
            metadata = {
                "process": process,
                "variation": variation,
                "nevts": sum(f["nevts"] for f in file_list),
                "xsec": XSEC_INFO[process],
            }
            fileset[f"{process}__{variation}"] = {"files": files, "metadata": metadata}

    return fileset


def main() -> None:
    parser = argparse.ArgumentParser(description="List the input files")
    parser.add_argument("--n-files", type=int, default=-1, help="Files per sample")
    parser.add_argument("--sample", help="Only this sample, like ttbar__nominal")
    parser.add_argument("--urls", action="store_true", help="Print each file URL")
    args = parser.parse_args()

    fileset = construct_fileset(args.n_files)
    if args.sample:
        fileset = {args.sample: fileset[args.sample]}

    for name, sample in fileset.items():
        if args.urls:
            print(*sample["files"], sep="\n")
        else:
            nevts = sample["metadata"]["nevts"]
            print(f"{name:28} {len(sample['files']):4} files {nevts:12,} events")


if __name__ == "__main__":
    main()
