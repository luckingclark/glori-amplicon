# Changelog

## Unreleased

- Move the complete walkthrough to bilingual guides in `docs/`, add concise bilingual input specifications, and use a short English repository README.
- Credit PKU-Gaolab and Ming-Ao Lu in authorship, citation metadata and the MIT notice for local contributions; preserve the original upstream license separately.

- Package a standalone amplicon workflow adapted from GLORI-tools, with explicit source attribution and retained licenses.
- Document installation and the complete workflow using users' own FASTQ and FASTA paths.
- Specify the required input files, content, orientation and naming rules in `docs/inputs.en.md` and `docs/inputs.zh-CN.md`.
- Retain the corrected statsmodels/SciPy interfaces and batched Step 1 writing.
- Stop on failed subprocesses; reject reuse of nonempty output directories and unsupported reverse alignments.
- Reject duplicate FASTQ read IDs before alignment without keeping all IDs in memory.
- Remove the inherited name-based rRNA depth exception: amplicon names containing `GL` now also use the requested pileup depth. Counts for these names can differ from older versions when the requested depth is not 10000.
- Separate sorting threads and memory from the mapping thread setting.
- Produce an explicitly empty, header-only FDR table when no sites pass.
- Add tests and a Linux CI configuration.
- Distribute no research data, sequence references, results, or downloadable example datasets.
