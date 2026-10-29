import uproot

from file_input import construct_fileset


def main() -> None:
    fileset = construct_fileset(n_files_max_per_sample=1)
    for name, sample in fileset.items():
        print(
            f"{name}: {len(sample['files'])} file(s), {sample['metadata']['nevts']} events"
        )

    url = fileset["single_top_tW__nominal"]["files"][0]
    with uproot.open(url) as f:
        events = f["Events"]
        print(f"\n{url}\n{events.num_entries} entries")
        print(events["Jet_pt"].array(entry_stop=5))


if __name__ == "__main__":
    main()
