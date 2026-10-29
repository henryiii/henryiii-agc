from file_input import construct_fileset

configfile: "config.yaml"

N_FILES = config["n_files_max_per_sample"]
SAMPLES = list(construct_fileset(N_FILES))


rule all:
    input:
        expand("results/histograms/{sample}.root", sample=SAMPLES),


rule histogram:
    input:
        "nanoaod_inputs.json",
        "file_input.py",
        script="histogram.py",
    output:
        "results/histograms/{sample}.root",
    params:
        n_files=N_FILES,
    shell:
        "python {input.script} {wildcards.sample} {output} --n-files {params.n_files}"
