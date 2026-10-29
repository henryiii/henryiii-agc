from file_input import construct_fileset

configfile: "config.yaml"

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
        "nanoaod_inputs.json",
        "file_input.py",
        script="histogram.py",
    output:
        "results/histograms/{sample}.root",
    params:
        n_files=N_FILES,
    # pelicanfs does not retry dropped connections
    retries: 3
    shell:
        "python {input.script} {wildcards.sample} {output} --n-files {params.n_files}"


rule merge:
    input:
        hists=expand("results/histograms/{sample}.root", sample=SAMPLES),
        script="merge.py",
    output:
        "results/histograms.root",
    shell:
        "python {input.script} {output} {input.hists}"


rule validate:
    input:
        hists="results/histograms.root",
        reference=REFERENCE,
        script="validate.py",
    output:
        "results/validation.txt",
    shell:
        "python {input.script} {input.hists} {input.reference} | tee {output}"


rule fit:
    input:
        "results/histograms.root",
        config="cabinetry_config.yml",
        script="fit.py",
    output:
        workspace="results/workspace.json",
        figures=directory("results/figures"),
        result="results/fit.txt",
    shell:
        "python {input.script} {input.config} {output.workspace} {output.figures}"
        " | tee {output.result}"
