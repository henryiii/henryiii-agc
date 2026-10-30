from agc.file_input import construct_fileset

configfile: "config/config.yaml"

N_FILES = config["n_files_max_per_sample"]
SAMPLES = list(construct_fileset(N_FILES))
REFERENCE = f"reference/histos_{'all' if N_FILES == -1 else N_FILES}_file_per_process.json"


rule all:
    input:
        "results/histograms.root",
        "results/validation.txt",
        "results/fit.txt",


rule histogram:
    input:
        "src/agc/nanoaod_inputs.json",
        "src/agc/file_input.py",
        "src/agc/histogram.py",
    output:
        "results/histograms/{sample}.root",
    params:
        n_files=N_FILES,
    # pelicanfs does not retry dropped connections
    retries: 3
    shell:
        "python -m agc.histogram {wildcards.sample} {output} --n-files {params.n_files}"


rule merge:
    input:
        "src/agc/merge.py",
        hists=expand("results/histograms/{sample}.root", sample=SAMPLES),
    output:
        "results/histograms.root",
    shell:
        "python -m agc.merge {output} {input.hists}"


rule validate:
    input:
        "src/agc/validate.py",
        hists="results/histograms.root",
        reference=REFERENCE,
    output:
        "results/validation.txt",
    shell:
        "python -m agc.validate {input.hists} {input.reference} | tee {output}"


rule fit:
    input:
        "results/histograms.root",
        "src/agc/fit.py",
        config="config/cabinetry.yml",
    output:
        workspace="results/workspace.json",
        figures=directory("results/figures"),
        result="results/fit.txt",
    shell:
        "python -m agc.fit {input.config} {output.workspace} {output.figures}"
        " | tee {output.result}"
