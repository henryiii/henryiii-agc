# henryiii-agc

A step-by-step port of the [Analysis Grand Challenge CMS open data ttbar
analysis](https://github.com/iris-hep/analysis-grand-challenge/tree/main/analyses/cms-open-data-ttbar).

The input NanoAOD files are read remotely from the CERN open data copy on the
OSDF, `pelican://osg-htc.org/cern-opendata/upload/agc/1.0.0`, with
[pelicanfs](https://github.com/PelicanPlatform/pelicanfs) and uproot. Nothing
is downloaded up front. `nanoaod_inputs.json` (from the AGC) lists the files.

## List the input files

These commands only read `nanoaod_inputs.json`; they do not access the files.

```bash
uv run file_input.py                          # samples, file and event counts
uv run file_input.py --n-files 1              # same, limited to 1 file per sample
uv run file_input.py --sample ttbar__nominal --urls  # pelican:// URLs
```

## Run the workflow

The workflow uses [Snakemake](https://snakemake.readthedocs.io). Outputs go to
`results/`. Set the number of files per sample in `config.yaml` (`-1` for all).

The workflow fills the `4j1b` (HT) and `4j2b` (trijet mass) histograms for
each sample, merges them into `results/histograms.root` with pseudodata, and
compares them with the AGC reference in `reference/`. The result of the
comparison is in `results/validation.txt`.

The nominal samples also get the systematic variations: jet pT scale
(`pt_scale_up`) and resolution (`pt_res_up`), b-tag weights
(`btag_var_{0..3}_{up,down}`), and W+jets scale (`scale_var_{up,down}`).
`pt_res_up` uses random smearing, so validation checks only its edges.

Use at most 2 jobs. With more, the OSDF caches can drop connections.

```bash
uv run snakemake -n                # dry run: show the jobs to run
uv run snakemake -c2               # run 2 jobs at a time
uv run snakemake -c2 --config n_files_max_per_sample=-1  # all files
uv run snakemake --summary         # status of each output file
```

To fill one sample without Snakemake:

```bash
uv run histogram.py ttbar__nominal results/histograms/ttbar__nominal.root --n-files 1
```

`uv run main.py` is a quick check that remote access works. It reads `Jet_pt`
from one file.

## Development

```bash
prek -a  # lint and format (ruff)
```
