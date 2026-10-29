import argparse
from pathlib import Path

import awkward as ak
import hist
import numpy as np
import uproot
import vector

from file_input import construct_fileset

vector.register_awkward()

STEP_SIZE = 500_000
LUMI = 3378  # /pb
B_TAG_THRESHOLD = 0.5
REGIONS = ("4j1b", "4j2b")

BRANCHES = [
    "Electron_pt",
    "Electron_eta",
    "Electron_cutBased",
    "Electron_sip3d",
    "Muon_pt",
    "Muon_eta",
    "Muon_tightId",
    "Muon_sip3d",
    "Muon_pfRelIso04_all",
    "Jet_pt",
    "Jet_eta",
    "Jet_phi",
    "Jet_mass",
    "Jet_btagCSVV2",
    "Jet_jetId",
]


def make_histograms() -> dict[str, hist.Hist]:
    return {
        region: hist.Hist.new.Reg(
            25, 50, 550, name="observable", label="observable [GeV]"
        ).Weight()
        for region in REGIONS
    }


def observables(events: ak.Array) -> dict[str, ak.Array]:
    """
    Select events and compute the observable for each region: HT in 4j1b, and
    the trijet mass in 4j2b.
    """
    electron_reqs = (
        (events.Electron_pt > 30)
        & (np.abs(events.Electron_eta) < 2.1)
        & (events.Electron_cutBased == 4)
        & (events.Electron_sip3d < 4)
    )
    muon_reqs = (
        (events.Muon_pt > 30)
        & (np.abs(events.Muon_eta) < 2.1)
        & events.Muon_tightId
        & (events.Muon_sip3d < 4)
        & (events.Muon_pfRelIso04_all < 0.15)
    )
    # Bit 2 of jetId is tight lepton veto (coffea's Jet.isTightLeptonVeto)
    jet_reqs = (
        (events.Jet_pt > 30)
        & (np.abs(events.Jet_eta) < 2.4)
        & ((events.Jet_jetId & 4) != 0)
    )

    jets = ak.zip(
        {
            "pt": events.Jet_pt,
            "eta": events.Jet_eta,
            "phi": events.Jet_phi,
            "mass": events.Jet_mass,
            "btag": events.Jet_btagCSVV2,
        },
        with_name="Momentum4D",
    )[jet_reqs]

    n_leptons = ak.sum(electron_reqs, axis=1) + ak.sum(muon_reqs, axis=1)
    n_btags = ak.sum(jets.btag > B_TAG_THRESHOLD, axis=1)
    base = (n_leptons == 1) & (ak.num(jets) >= 4)

    jets_4j1b = jets[base & (n_btags == 1)]
    ht = ak.sum(jets_4j1b.pt, axis=1)

    # Hadronic top: the trijet with at least one b-tag and the largest pT
    jets_4j2b = jets[base & (n_btags >= 2)]
    trijet = ak.combinations(jets_4j2b, 3, fields=["j1", "j2", "j3"])
    p4 = trijet.j1 + trijet.j2 + trijet.j3
    max_btag = np.maximum(trijet.j1.btag, np.maximum(trijet.j2.btag, trijet.j3.btag))
    p4 = p4[max_btag > B_TAG_THRESHOLD]
    trijet_mass = ak.flatten(p4[ak.argmax(p4.pt, axis=1, keepdims=True)].mass)

    return {"4j1b": ht, "4j2b": trijet_mass}


def fill_histograms(files: list[str], xsec_weight: float) -> dict[str, hist.Hist]:
    hists = make_histograms()
    # A memory-size step_size reads every basket key one at a time, which is
    # very slow over high-latency remote access (scikit-hep/uproot5#1797).
    for events in uproot.iterate(
        {f: "Events" for f in files}, BRANCHES, step_size=STEP_SIZE
    ):
        for region, observable in observables(events).items():
            hists[region].fill(
                observable=observable,
                weight=np.full(len(observable), xsec_weight),
            )
    return hists


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill histograms for one sample")
    parser.add_argument("sample", help="Fileset key, like ttbar__nominal")
    parser.add_argument("output", type=Path, help="Output ROOT file")
    parser.add_argument("--n-files", type=int, default=-1)
    args = parser.parse_args()

    sample = construct_fileset(args.n_files)[args.sample]
    metadata = sample["metadata"]
    xsec_weight = metadata["xsec"] * LUMI / metadata["nevts"]
    hists = fill_histograms(sample["files"], xsec_weight)

    suffix = "" if metadata["variation"] == "nominal" else f"_{metadata['variation']}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with uproot.recreate(args.output) as f:
        for region, h in hists.items():
            f[f"{region}_{metadata['process']}{suffix}"] = h


if __name__ == "__main__":
    main()
