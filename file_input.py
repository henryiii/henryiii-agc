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
