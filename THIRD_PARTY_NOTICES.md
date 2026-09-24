# Code and method provenance

This repository is an unofficial, targeted-amplicon adaptation of GLORI-tools. It does not claim ownership of the original GLORI method, official endorsement, or novelty of the underlying conversion and statistical algorithms.

**Authors of this adaptation: PKU-Gaolab, Ming-Ao Lu.** Their credit and 2026 copyright notice apply to the local additions, modifications and documentation, not to ownership of the upstream work.

| Component | Provenance | Licensing and treatment |
|---|---|---|
| `pipelines/*.py` | Adapted local copies of GLORI-tools helper programs | Preserve existing attribution headers and the upstream MIT notice in `LICENSE`. Local changes are described below. |
| `run_GLORI_amplicon.py` | Local amplicon entry point incorporating and adapting GLORI-tools mapping, A-restoration and calling workflow | The copied upstream portions remain under the preserved MIT notice. This entry point is not asserted to exist in the upstream repository or to be authored by the upstream maintainers. |
| `prepare_amplicon_ref.py` | Local builder adapting reference conversion/indexing and single-base annotation for short target sequences | Included as part of this amplicon adaptation; no claim that it is an upstream GLORI-tools file. |
| README, bilingual guides, environment and tests | Packaging and usability additions for this adaptation | MIT, with the adaptation's 2026 copyright notice retained in `LICENSE`. |
| RNA-m5C | An upstream source acknowledged by GLORI-tools | MIT attribution is preserved in `LICENSES/RNA-m5C-MIT.txt`. This does not assert that every local file was copied directly from RNA-m5C. |
| Zenodo DOI `10.5281/zenodo.14233421` | Referenced companion shell/R/Perl workflows for the GLORI 3.0 paper | The record declares CC BY 4.0. Those companion files are not bundled. Method/command references are acknowledged in `CITATIONS.md`; its license is not silently relabeled MIT. |
| GLORI and GLORI 3.0 papers | Scientific method references | Cited by DOI; no paper PDFs, figures or screenshots are redistributed. |

**Retained licenses.** `LICENSE` retains “Copyright (c) 2022 Cong Liu” and the complete MIT text, and adds “Copyright (c) 2026 PKU-Gaolab, Ming-Ao Lu” for this adaptation's contributions. The original GLORI-tools license is also preserved unchanged in `LICENSES/GLORI-tools-MIT.txt`. `LICENSES/RNA-m5C-MIT.txt` retains the upstream RNA-m5C notice. Third-party dependency licenses continue to apply to those separately installed programs.

**Changes in the local adaptation.** The workflow uses user-provided amplicon FASTA instead of whole-genome/transcriptome resources, creates a small Bowtie1 reference, preserves the A→G mapping/A restoration strategy and upstream calling thresholds, supports an uncompressed or gzipped single-end input, updates the SciPy/statsmodels interfaces, and batches the Step 1 text writes. Release preparation additionally stops on subprocess failure, separates sorting memory settings from mapping threads, checks reference/input assumptions, refuses nonempty output directories, rejects unsupported reverse alignments, and emits a header-only FDR table when there are no calls. These engineering changes do not constitute a newly invented GLORI method.

**Additional input/depth safeguards.** Duplicate FASTQ read identifiers are rejected before alignment. The inherited special case for reference names containing `GL` has been removed: all amplicons now use the requested pileup depth and window size. This intentionally changes the former hidden behavior for such names when a nondefault depth is requested; it does not change the A/G counting or statistical formulas.

**Version provenance.** The starting point is the locally supplied GLORI-tools code and local amplicon adaptations. The exact upstream commit of that historical copy is unknown; no commit ID or release equivalence is invented. Consult the original sources at https://github.com/liucongcas/GLORI-tools and https://github.com/SYSU-zhanglab/RNA-m5C .

**Publication boundary.** The published MIT code may be copied and modified while preserving its notice. If any local additions were supplied separately by another person, their permission must cover those additions too; an upstream license does not assign authorship of later private changes. If a future revision copies substantial code from the CC BY 4.0 Zenodo files, it must also preserve that source's attribution, license link and change notice, rather than describing those imported portions as exclusively MIT.

**Data.** No real study data, sequence reference, sample-specific result, or downloadable synthetic example dataset is included. Users supply their own files. Software licenses do not grant rights to publish other people's experimental data.
