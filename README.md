# GLORI Amplicon

An unofficial adaptation of [GLORI-tools](https://github.com/liucongcas/GLORI-tools) for single-end, targeted amplicon m6A analysis.

**Authors of this adaptation: PKU-Gaolab, Ming-Ao Lu.**

The workflow prepares a custom amplicon reference, performs A-to-G conversion and Bowtie1 alignment, restores original read bases, and applies the upstream site-calling and FDR workflow. It includes a Conda environment and detailed English and Chinese instructions. Original algorithms and experimental methods are credited to their authors; this is not an official GLORI release.

## Documentation

| Document | English | 简体中文 |
|---|---|---|
| Complete installation and analysis guide | [User guide](docs/usage.en.md) | [操作指南](docs/usage.zh-CN.md) |
| Required input files and formats | [Input requirements](docs/inputs.en.md) | [输入文件规范](docs/inputs.zh-CN.md) |

Start with the input requirements, then follow the guide for your language. Documentation is tracked in `docs/` alongside the code and is included in source downloads.

## Requirements and installation

- Linux, Bash and Conda; Slurm instructions are included for cluster users.
- One selected read end per sample, aligned forward to an RNA-oriented amplicon reference.
- Your own demultiplexed FASTQ and original, unconverted amplicon FASTA.
- A library without molecular UMIs for the direct workflow described here.

From the downloaded repository directory:

```bash
export CONDA_CHANNEL_PRIORITY=strict
conda env create --file environment.yml
conda activate glori_amplicon
```

The environment installs Python 3.10, Bowtie1, SAMtools, Trim Galore, Cutadapt and the required analysis libraries. Continue with the [step-by-step guide](docs/usage.en.md) for adapter trimming, reference preparation and analysis commands. No whole-genome reference or GTF is needed.

## Outputs and scope

Outputs include an indexed BAM, estimated conversion rates, and a tab-separated site table named `*.totalm6A.FDR.csv`. Positions refer to the original amplicon FASTA using 1-based coordinates. A header-only table means that no sites passed the selected filters; it does not establish zero methylation.

The current workflow does not support paired-end alignment, automatic UMI processing or reverse-read quantification. It retains upstream background estimation and filtering assumptions: read A-count and depth cutoffs affect counts, and FDR is applied to prefiltered candidates. Read counts are not independent molecule counts without UMIs. See the guide for interpretation and limitations.

No experimental data, reference sequences, result tables or downloadable example datasets are distributed.

## Validation and support

Run checks from the repository root in the documented environment:

```bash
python -m unittest discover -s tests -v
```

Tests generate minimal inputs in temporary directories. On 2026-09-24, [Linux checks](https://github.com/luckingclark/glori-amplicon/actions/runs/35950393337) passed on Ubuntu 24.04 with the documented Conda environment: dependency and command-line checks succeeded, and all 12 tests passed, including full pipeline checks. This verifies software execution on the test inputs, not biological accuracy or performance on every dataset.

For help, open an issue with software versions, the failed step and a command/error message with private paths and study identifiers removed. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Citation and provenance

Please cite the original [GLORI paper](https://doi.org/10.1038/s41587-022-01487-9) and [GLORI-tools](https://github.com/liucongcas/GLORI-tools), together with the [GLORI 3.0 paper](https://doi.org/10.1038/s41592-025-02680-9) and [companion code](https://doi.org/10.5281/zenodo.14233421) when that experimental method applies. Record the repository URL and commit/release used for this adaptation.

See [CITATIONS.md](CITATIONS.md), [CITATION.cff](CITATION.cff), [AUTHORS.md](AUTHORS.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for references, authorship and modification provenance.

## License

[MIT](LICENSE). The original GLORI-tools notice is retained, with an additional notice for modifications and documentation by PKU-Gaolab, Ming-Ao Lu. Original GLORI-tools and RNA-m5C notices are also preserved in [LICENSES/](LICENSES/). Third-party dependency licenses remain applicable. The separately licensed Zenodo companion scripts and paper materials are not bundled.
