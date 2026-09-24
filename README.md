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

For help, open an issue with software versions, the failed step and a command/error message with private paths and study identifiers removed. Do not include confidential data or credentials. For code changes, explain the change, run the checks above, and update both language guides when commands or inputs change.

## Citation and provenance

For this adaptation, cite **PKU-Gaolab, Ming-Ao Lu. GLORI Amplicon**, with the [repository URL](https://github.com/luckingclark/glori-amplicon) and commit or release used. Machine-readable citation information is available in [CITATION.cff](CITATION.cff).

Please also cite the original methods and software below. Cite GLORI 3.0 when that experimental method applies; using this software alone does not establish which wet-lab method generated the data.

1. Liu, C., Sun, H., Yi, Y., et al. (2023). **Absolute quantification of single-base m6A methylation in the mammalian transcriptome using GLORI.** *Nature Biotechnology*, 41, 355–366. https://doi.org/10.1038/s41587-022-01487-9 . First published online in 2022; the volume year is 2023.
2. Sun, H., Lu, B., Zhang, Z., et al. (2025). **Mild and ultrafast GLORI enables absolute quantification of m6A methylome from low-input samples.** *Nature Methods*, 22, 1226–1236. https://doi.org/10.1038/s41592-025-02680-9 . Cite this when the GLORI 3.0 experimental method is used; software use alone does not establish which wet-lab method generated a dataset.
3. Lu, B. (2024). **Codes for “Mild and ultrafast GLORI enables absolute quantification of m6A methylome from low-input samples”.** Zenodo. https://doi.org/10.5281/zenodo.14233421 . This is a separate collection of companion analysis scripts, not a release of this amplicon adaptation.
4. **GLORI-tools**, by Cong Liu and contributors. https://github.com/liucongcas/GLORI-tools . Its upstream software citation points to https://doi.org/10.5281/zenodo.7014168 . This repository is not asserted to be an exact copy of that archived version.
5. **RNA-m5C**, SYSU-zhanglab and Jianheng Liu. https://github.com/SYSU-zhanglab/RNA-m5C . This is an upstream code source acknowledged by GLORI-tools.


Cite analysis dependencies as appropriate for your work. Code sources and the scope of local changes are described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

Original additions, modifications, and documentation by PKU-Gaolab, Ming-Ao Lu are licensed under the [MIT License](LICENSE). Portions derived from GLORI-tools and RNA-m5C retain their original copyright and MIT license notices in [LICENSES/](LICENSES/); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for their scope. This independent adaptation does not imply collaboration with or endorsement by the upstream authors. Third-party dependency licenses remain applicable. Zenodo companion scripts and paper materials are not bundled.
