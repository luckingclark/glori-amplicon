# GLORI Amplicon

Analyze **targeted amplicon m6A sequencing with GLORI**, from your FASTQ reads and original amplicon sequences to an aligned BAM, conversion-rate estimates, and a filtered table of candidate m6A sites. This command-line workflow is for researchers working with a small set of custom amplicon references.

This is an independent, unofficial adaptation of [GLORI-tools](https://github.com/liucongcas/GLORI-tools). It uses the upstream conversion, alignment and site-calling approach; it is not an official GLORI release or a new detection method.

## Before you start

- Use **Linux, Bash and Conda**. On Slurm, obtain a compute-node allocation before processing reads; see the [cluster instructions](docs/usage.en.md#4-request-cluster-resources).
- Supply your own demultiplexed FASTQ and original amplicon FASTA. **No experimental data, reference sequences or downloadable example datasets are included.**
- Analyze one sample and one selected read end per run. For paired-end sequencing, choose the end that aligns forward to the RNA-oriented reference; R1 is not necessarily correct for every library.
- The direct workflow assumes no molecular UMIs. i5/i7 sample indexes are not UMIs. Paired-end alignment, automatic UMI processing and reverse-read quantification are not supported.

| Required file | What it must contain |
|---|---|
| FASTQ (`.fq`, `.fastq`, or gzip-compressed with `.gz`) | Four-line records with Phred+33 qualities; unique read identifiers before the first whitespace; one selected read end |
| Original FASTA (`.fa` or `.fasta`, uncompressed) | Complete target amplicon sequences in original RNA 5'-to-3' orientation, with T for U and original A bases preserved; not merely two primers or a consensus of converted reads |

Use original, unconverted `A/C/G/T/N` reference sequences with unique IDs and at least one A per record. Exclude sequencing adapters. Quantified sites should lie outside primer-derived regions, which the software does not mask automatically. Check the detailed ID and sequence rules in the input requirements below. No whole-genome reference or GTF is needed.

**First time here?** Read the input requirements, then use the guide in your preferred language for explanations of each command. The quick start below follows the same workflow.

| Documentation | English | Chinese version |
|---|---|---|
| Installation, Slurm and step-by-step analysis | [User guide](docs/usage.en.md) | [User guide in Chinese](docs/usage.zh-CN.md) |
| File formats and reference design | [Input requirements](docs/inputs.en.md) | [Input requirements in Chinese](docs/inputs.zh-CN.md) |

## 1. Install the environment

Download the repository using **Code > Download ZIP**, extract it, and transfer the complete code directory to Linux. Keep `pipelines/` alongside the two entry-point scripts. Access to a private repository requires GitHub authorization.

Replace `/path/to/your/glori-amplicon` with the extracted code directory. Run these commands in Bash:

```bash
cd /path/to/your/glori-amplicon
export CONDA_CHANNEL_PRIORITY=strict
conda env create --file environment.yml
conda activate glori_amplicon
python prepare_amplicon_ref.py --help
python run_GLORI_amplicon.py --help
```

The two Python commands should display usage information and exit successfully. Create the environment once; activate it again in each new session. If the name already exists or Conda is not initialized, follow the [installation guide](docs/usage.en.md#3-create-the-conda-environment--once-before-first-use).

[environment.yml](environment.yml) specifies Python 3.10, Bowtie **1.3.1**, SAMtools, Trim Galore **0.6.10**, Cutadapt 4.x, SeqKit, FastQC, Biopython, pysam, NumPy, pandas, SciPy and statsmodels. Bowtie2 is not a substitute. The file is a dependency specification, not an exact build lockfile; installed builds can differ between systems.

## 2. Run one sample

This example is a complete command sequence **after you supply the inputs**; it is not a bundled demonstration dataset. It assumes standard Illumina sequencing adapters and uses `sample1_R1.fq.gz` as the input filename. Match the adapter option to your library; if your filename differs, also update the trimmed filename below.

Replace the code, input and analysis paths with your own. Use a new sample working directory outside the code directory, activate the environment, and run each step in order. Stop and resolve any error before continuing.

### Prepare the working directory and trim reads

```bash
conda activate glori_amplicon
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p /path/to/your/analysis/sample1
cd /path/to/your/analysis/sample1
mkdir -p trimmed qc
cp /path/to/your/data/amplicons.fa reference.fa

gzip -t /path/to/your/data/sample1_R1.fq.gz
trim_galore --illumina -q 20 --stringency 5 -e 0.1 --length 25 --dont_gzip -o trimmed /path/to/your/data/sample1_R1.fq.gz
seqkit stats trimmed/sample1_R1_trimmed.fq
fastqc -t 2 -o qc trimmed/sample1_R1_trimmed.fq
```

`gzip -t` should exit successfully without output. After trimming, `seqkit stats` should report nonzero reads. Review the FastQC HTML in `qc/`. The trimming example discards reads shorter than 25 nt; reassess this for shorter targets. High duplication is expected for many amplicon designs and is not a reason to deduplicate non-UMI reads by sequence or coordinates.

### Build the reference and run analysis

Stay in the sample working directory:

```bash
python /path/to/your/glori-amplicon/prepare_amplicon_ref.py -f reference.fa -pre panel -o ref -p 4

python /path/to/your/glori-amplicon/run_GLORI_amplicon.py \
  -q trimmed/sample1_R1_trimmed.fq \
  -f ref/panel.AG_conversion.fa -f2 reference.fa -b ref/panel.baseanno \
  -pre sample1 -o output -T 4 \
  --sort-threads 2 --sort-memory 256M \
  -m 2 -M 10000 --cutoff 3 --keep-tmp
```

The reference builder creates the converted FASTA, Bowtie indexes, annotation and FASTA indexes; it also writes `reference.fa.fai` beside the original reference. `-f` takes the converted reference, while `-f2` takes the original. The main script locates `pipelines/` automatically.

`--keep-tmp` retains alignment reports and intermediate counts. `-T` does not speed up the single-process conversion step; sorting has separate thread/memory settings. See the [parameter guide](docs/usage.en.md#8-run-the-amplicon-analysis) for filters and resource choices.

**For a rerun, use a new or empty result directory**, such as `-o output_retry1`; the program refuses a nonempty directory. The reference builder also refuses to overwrite an existing reference prefix.

## 3. Check the results

A successful main-program run exits with code 0 and prints `GLORI Amplicon Analysis Complete!`. Check the files as well:

```bash
samtools quickcheck output/sample1_r.sorted.bam
samtools view -c output/sample1_r.sorted.bam
samtools view -c -f 16 output/sample1_r.sorted.bam
cat output/tmp/sample1.sam.output
head -n 5 output/sample1.totalCR.txt
head -n 5 output/sample1.totalm6A.FDR.csv
```

`samtools quickcheck` should return successfully with no output. The alignment count should be positive; the reverse-alignment count (`-f 16`) should be zero. The program stops on unmapped-only input or detected reverse alignments.

| Output under `output/` | Meaning |
|---|---|
| `sample1_r.sorted.bam` and `.bam.bai` | Sorted, indexed alignment with original read bases restored |
| `sample1.totalCR.txt` | Estimated background A-to-G conversion rates; inspect values alongside your controls |
| `sample1.totalm6A.FDR.csv` | Sites passing candidate filters and FDR; **tab-separated despite the `.csv` extension** |
| `tmp/sample1.sam.output` | Bowtie alignment statistics, retained with `--keep-tmp` |
| `tmp/sample1.totalformat.txt` | Intermediate site counts, retained with `--keep-tmp` |

In the site table, `Sites` is **1-based on the original amplicon FASTA**, not a genomic coordinate. `Ratio` is `Acov / AGcov`, the observed A-retention proportion under the selected filters; `P_adjust` is the adjusted P value. Full column descriptions are in the [result guide](docs/usage.en.md#9-check-the-results).

**A header-only site table is a valid zero-candidate/zero-passing-site output, not evidence of zero methylation.** Missing sites may fail coverage or other filters. A missing table is an error. See [result interpretation](docs/usage.en.md#9-check-the-results) and [limitations](docs/usage.en.md#11-interpretation-and-limitations).

A retention ratio does not automatically correct incomplete conversion or amplification bias. Without UMIs, reads are not independent RNA molecules. Read A-count/depth filters affect counts, and FDR is calculated over prefiltered candidates. Interpret results with appropriate controls and replicates.

## Validation

On 2026-09-24, [Linux checks](https://github.com/luckingclark/glori-amplicon/actions/runs/35950393337) passed on Ubuntu 24.04: Conda environment creation, dependency and CLI checks, and all 12 tests, including reference preparation and the core analysis pipeline on temporary test inputs. This does not establish biological accuracy, performance on your dataset, or end-to-end adapter-trimming validation. The subsequent documentation changes leave the tested code and environment unchanged.

To run the checks yourself, return to the code directory with the environment active:

```bash
cd /path/to/your/glori-amplicon
python -m unittest discover -s tests -v
```

Under the documented Linux environment, expect the test summary `Ran 12 tests` followed by `OK`, with no skipped tests. Tests create temporary inputs; they do not require your research data.

## Author, licensing and citation

The amplicon adaptation and documentation are by **PKU-Gaolab, Ming-Ao Lu**. Source code and issue reports are hosted in [luckingclark/glori-amplicon](https://github.com/luckingclark/glori-amplicon).

For a problem report, open a repository issue with versions, the failed step and a command/error message with private paths and study identifiers removed. Do not post confidential data or credentials. For code changes, explain the change, run the checks, and update both language guides when commands or inputs change.


- **Local additions, modifications and documentation:** [MIT License](LICENSE).
- **Code derived from GLORI-tools:** retain the original [GLORI-tools MIT notice](LICENSES/GLORI-tools-MIT.txt).
- **Upstream RNA-m5C code:** retain the original [RNA-m5C MIT notice](LICENSES/RNA-m5C-MIT.txt).

Keep applicable copyright and license notices when redistributing the code. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) describes sources, modification scope and the separation of local and upstream contributions. Upstream attribution does not imply collaboration or endorsement. Separately installed dependencies retain their own licenses; the separately licensed Zenodo companion scripts and paper materials are not bundled.

<a id="citation-and-provenance"></a>

Cite this adaptation using [CITATION.cff](CITATION.cff), together with the repository URL and the commit or release used. Also cite the original methods and software below. Cite GLORI 3.0 when that experimental method applies; software use alone does not identify the wet-lab method.

1. Liu, C., Sun, H., Yi, Y., et al. (2023). **Absolute quantification of single-base m6A methylation in the mammalian transcriptome using GLORI.** *Nature Biotechnology*, 41, 355–366. https://doi.org/10.1038/s41587-022-01487-9 . First published online in 2022; the volume year is 2023.
2. Sun, H., Lu, B., Zhang, Z., et al. (2025). **Mild and ultrafast GLORI enables absolute quantification of m6A methylome from low-input samples.** *Nature Methods*, 22, 1226–1236. https://doi.org/10.1038/s41592-025-02680-9 . Cite this when the GLORI 3.0 experimental method is used; software use alone does not establish which wet-lab method generated a dataset.
3. Lu, B. (2024). **Codes for “Mild and ultrafast GLORI enables absolute quantification of m6A methylome from low-input samples”.** Zenodo. https://doi.org/10.5281/zenodo.14233421 . This is a separate collection of companion analysis scripts, not a release of this amplicon adaptation.
4. **GLORI-tools**, by Cong Liu and contributors. https://github.com/liucongcas/GLORI-tools . Its upstream software citation points to https://doi.org/10.5281/zenodo.7014168 . This repository is not asserted to be an exact copy of that archived version.
5. **RNA-m5C**, SYSU-zhanglab and Jianheng Liu. https://github.com/SYSU-zhanglab/RNA-m5C . This is an upstream code source acknowledged by GLORI-tools.


Cite analysis dependencies as appropriate for your work.
