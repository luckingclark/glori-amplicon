# GLORI Amplicon user guide

[Chinese version](usage.zh-CN.md) | [Repository overview](../README.md) | [Input requirements](inputs.en.md)

An unofficial amplicon adaptation of [GLORI-tools](https://github.com/liucongcas/GLORI-tools). The original GLORI algorithms and experimental methods are credited to their authors. This repository provides an amplicon reference builder, an adapted analysis entry point, dependencies and a step-by-step guide. It is not an official GLORI release or a new m6A detection method.

The adaptation also references the [GLORI 3.0 companion code](https://doi.org/10.5281/zenodo.14233421) and [GLORI 3.0 paper](https://doi.org/10.1038/s41592-025-02680-9). It is intended for single-end GLORI analysis against a small set of custom amplicons. See [source and license notices](../THIRD_PARTY_NOTICES.md) and [references](../README.md#citation-and-provenance).

**No experimental data, synthetic example dataset, reference sequences or result tables are distributed.** Supply your own FASTQ and FASTA. `sample1` is only a placeholder output name.

Read the [input requirements](inputs.en.md) first: you need one selected read end for a sample and its original amplicon FASTA. That document explains formats, orientation, primer regions and generated files.

## 1. Scope and workflow

```text
Your single-end FASTQ
  → Trim Galore: remove sequencing adapters and low-quality ends
  → Build an A→G reference and indexes from the original amplicon FASTA
  → Convert read A→G, align with Bowtie1, restore original read A positions
  → Pileup, site counts, background testing and FDR correction
  → Site table, conversion rates and BAM
```

Use **Linux, Bash and Conda**, optionally on a Slurm cluster. Windows can be used to download and transfer files; do not paste these Bash commands directly into Windows PowerShell.

The direct workflow assumes **no molecular UMI**. i5/i7 sample indexes are not molecular UMIs. If your library has UMIs, process them according to the actual library design first; the pipeline does not identify or remove them automatically. Do not deduplicate non-UMI short amplicon reads solely by sequence or alignment coordinates.

Select one read end whose orientation matches the original RNA / forward FASTA and supports A→G analysis. You can select the appropriate end from paired-end sequencing. The guide uses `sample1_R1.fq.gz`, but **R1 is not necessarily the correct end for every library**. The program stops if reverse alignments are detected, rather than reporting unsupported quantification.

A whole human/mouse genome, STAR indexes, a genome-wide GTF and R are not required.

## 2. Download the code and identify your directories

On this repository's GitHub page, choose **Code → Download ZIP**, extract it, and transfer the complete code directory to Linux. Git cloning is also possible, but is not required for this guide.

All paths below are placeholders. **Replace them with your own paths before running commands.** Do not literally create `/path/to/your` at the system root.

| Placeholder | Replace with |
|---|---|
| `/path/to/your/glori-amplicon` | Extracted code directory containing README.md and the two main programs |
| `/path/to/your/data` | Directory holding your original FASTQ and amplicon FASTA |
| `/path/to/your/analysis/sample1` | Working directory for this sample's trimmed reads, indexes and results |
| `/path/to/your/miniforge3` | Your Conda installation directory, used only if shell initialization is needed |

Prefer simple paths using letters, numbers, underscores and hyphens. Inputs and outputs may be on different disks. You need permission to read inputs and write the working directory, with sufficient space for uncompressed reads, SAM, BAM and intermediate files.

The code directory should contain at least:

```text
glori-amplicon/
├── README.md
├── docs/  # English and Chinese guides and input requirements
├── environment.yml
├── LICENSE
├── LICENSES/
├── THIRD_PARTY_NOTICES.md
├── prepare_amplicon_ref.py
├── run_GLORI_amplicon.py
├── pipelines/
└── tests/
```

## 3. Create the Conda environment — once, before first use

If your cluster provides Conda, load it according to the cluster documentation, then check:

```bash
conda --version
```

This should print a Conda version. If the command is unavailable, load the appropriate cluster module or install [Miniforge](https://github.com/conda-forge/miniforge). The procedure depends on the cluster; this project does not assume an administrator's installation path.

Enter the code directory and create the environment:

```bash
cd /path/to/your/glori-amplicon
export CONDA_CHANNEL_PRIORITY=strict
conda env create --file environment.yml
conda activate glori_amplicon
```

| Command | Purpose |
|---|---|
| `cd ...` | Enter the code directory |
| `export CONDA_CHANNEL_PRIORITY=strict` | Use strict package-channel priority in this terminal |
| `conda env create --file environment.yml` | Create the environment named `glori_amplicon` using the supplied dependency file |
| `conda activate glori_amplicon` | Use its software; the prompt usually shows `(glori_amplicon)` |

Activation uses an environment name, not a project-path variable. `environment.yml` contains no personal `prefix` or absolute installation path. It is a dependency specification, not a cross-platform build lockfile.

| Software | Purpose |
|---|---|
| Python 3.10, Biopython, pysam | Run scripts and read/write sequences and alignments |
| numpy, pandas, scipy, statsmodels | Numerical work, tables and statistical tests |
| Bowtie 1.3.1 | Amplicon alignment; Bowtie2 is not a substitute |
| samtools | FASTA indexing, BAM sorting and checks |
| Trim Galore 0.6.10, Cutadapt 4.x | Adapter and quality trimming |
| SeqKit, FastQC | Read counts, lengths and quality reports |

If the environment name already exists, try activating and checking it first; do not delete your old environment. Alternatively, use `conda env create --name your_glori_env --file environment.yml`, then activate it with `conda activate your_glori_env`.

Check the installation:

```bash
python -c "import numpy, pandas, scipy, statsmodels, Bio, pysam; from statsmodels.stats.multitest import multipletests; print('Python dependencies OK')"
bowtie --version
samtools --version
trim_galore --version
cutadapt --version
seqkit version
fastqc --version
python prepare_amplicon_ref.py --help
python run_GLORI_amplicon.py --help
```

The first command should print `Python dependencies OK`; the others should print versions or help. Resolve installation errors before processing data.

After logging in again, usually only `conda activate glori_amplicon` is needed. If Conda reports that your shell is not initialized, use your actual installation path:

```bash
source /path/to/your/miniforge3/etc/profile.d/conda.sh
conda activate glori_amplicon
```

## 4. Request cluster resources

Skip this section on a regular Linux workstation. On Slurm, process data on an allocated compute node. From a login node, request an interactive shell:

```bash
srun --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=16G --time=08:00:00 --pty bash
```

This requests one node, one task, eight CPU cores, 16 GB memory and up to eight hours. Account, partition and resource limits depend on your cluster. If required, add `--partition=your_actual_partition`; `sinfo -s` lists partitions. Do not request another allocation if you are already in an allocated compute-node session.

Activate the environment on the compute node and limit extra numerical-library threads:

```bash
conda activate glori_amplicon
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
```

If activation is unavailable in the new shell, run the preceding section's `source` command first. The final line limits extra threads spawned by mathematical libraries, avoiding excessive CPU use across multiple processes.

Keep your connection open during an interactive run. For long jobs that must survive disconnection, use your cluster's batch-job instructions; do not run large analyses in the background on the login node.

## 5. Prepare your FASTQ and original reference

See [input requirements](inputs.en.md) for format, source and preparation rules. The following names match the commands below; use your actual names consistently.

| File | Requirements |
|---|---|
| `/path/to/your/data/sample1_R1.fq.gz` | One selected read end for one demultiplexed sample; four-line FASTQ, Phred+33, unique read IDs |
| `/path/to/your/data/amplicons.fa` | Uncompressed original FASTA with one or more amplicons, before A→G conversion; not merely two primer sequences |

Each FASTA record starts with `>` followed by your amplicon ID; the subsequent line(s) contain its sequence. Use the known original target and **retain its original A bases**. Do not use a consensus of GLORI-converted reads as the original reference.

Use the original RNA's 5′→3′ orientation with DNA letters `A/C/G/T`, replacing RNA U with T. `N` is allowed but can affect alignment and is not a quantifiable A site; other ambiguous letters are rejected. Every reference record must contain at least one original A. IDs must be unique, without spaces; start with a letter or digit and use only letters, digits, underscores, dots or hyphens. IDs must not contain `_AG_converted` anywhere.

The reference should represent the target fragment to be aligned after sequencing-adapter removal, without sequencing adapters. Quantified sites should lie outside regions whose bases are directly supplied by PCR primers. The program does not infer primer boundaries or distinguish primer-derived bases from template-derived bases automatically.

Create a working directory:

```bash
mkdir -p /path/to/your/analysis/sample1
cd /path/to/your/analysis/sample1
mkdir -p trimmed qc
cp /path/to/your/data/amplicons.fa reference.fa
```

`mkdir -p` creates directories; `cd` enters the working directory; `cp` copies your reference there as `reference.fa`. You do not need to copy or manually decompress the raw FASTQ first.

Check the inputs:

```bash
gzip -t /path/to/your/data/sample1_R1.fq.gz
seqkit stats /path/to/your/data/sample1_R1.fq.gz
cat reference.fa
```

`gzip -t` normally produces no output on success, indicating readable compressed content. `seqkit stats` reports read counts and lengths; `num_seqs` should not be zero. `cat` displays your short reference for manual confirmation of the target.

## 6. Trim sequencing adapters and low-quality ends

The command below assumes standard Illumina adapters. For another adapter design, adjust the parameters to match your library rather than blindly using this setting.

```bash
trim_galore --illumina -q 20 --stringency 5 -e 0.1 --length 25 --dont_gzip -o trimmed /path/to/your/data/sample1_R1.fq.gz
```

| Parameter | Meaning |
|---|---|
| `--illumina` | Detect the standard Illumina adapter `AGATCGGAAGAGC` |
| `-q 20` | Trim using a Phred quality threshold of 20 |
| `--stringency 5` | Require an adapter overlap of at least five bases |
| `-e 0.1` | Allow an adapter-match error rate of 0.1 |
| `--length 25` | Discard reads shorter than 25 nt after trimming; reassess for shorter targets |
| `--dont_gzip` | Write an uncompressed `.fq` |
| `-o trimmed` | Write to `trimmed` in the current working directory |

Only one end is used, so there is no `--paired` option. For input `sample1_R1.fq.gz`, expect `trimmed/sample1_R1_trimmed.fq`; other input names produce corresponding output names.

```bash
seqkit stats trimmed/sample1_R1_trimmed.fq
fastqc -t 2 -o qc trimmed/sample1_R1_trimmed.fq
```

The first command checks trimmed read counts and lengths. The second produces a FastQC HTML report that you can download and open locally. Amplicon reads concentrate on the same fragment, so high duplication and unusual base composition do not automatically indicate failure. Do not deduplicate by sequence merely to remove these warnings.

## 7. Prepare the A→G reference and indexes

Stay in `/path/to/your/analysis/sample1` and run:

```bash
python /path/to/your/glori-amplicon/prepare_amplicon_ref.py -f reference.fa -pre panel -o ref -p 4
```

| Parameter | Meaning |
|---|---|
| `-f reference.fa` | Your original, unconverted reference |
| `-pre panel` | Prefix for generated reference files; need not match the sample name |
| `-o ref` | Directory for generated references and indexes |
| `-p 4` | Four threads for Bowtie index construction |

The program creates `ref/panel.AG_conversion.fa`, six `.ebwt` Bowtie index files and `ref/panel.baseanno`. It also creates `.fai` indexes for both the original and converted FASTA, so the original reference directory must be writable.

```bash
ls ref
```

Confirm these files exist. Original A bases remain unchanged in `reference.fa`; the A→G version is a separate file.

## 8. Run the amplicon analysis

```bash
python /path/to/your/glori-amplicon/run_GLORI_amplicon.py -q trimmed/sample1_R1_trimmed.fq -f ref/panel.AG_conversion.fa -f2 reference.fa -b ref/panel.baseanno -pre sample1 -o output -T 4 --sort-threads 2 --sort-memory 256M -m 2 -M 10000 --cutoff 3 --keep-tmp
```

The script automatically locates the adjacent `pipelines` directory. You do not need to set `$PROJECT`, modify `PYTHONPATH` or edit installation paths inside scripts.

| Parameter | Meaning |
|---|---|
| `-q` | Trimmed FASTQ |
| `-f` | A→G reference for alignment |
| `-f2` | Original reference for identifying original A positions |
| `-b` | Generated annotation, enabling per-amplicon background estimation |
| `-pre sample1` | Output filename prefix |
| `-o output` | Result directory, which must be new or empty |
| `-T 4` | Alignment and some downstream threads/processes; Step 1 remains single-process |
| `--sort-threads 2` | samtools sorting's extra threads, in addition to its main thread, independent of `-T` |
| `--sort-memory 256M` | Approximate memory per sorting thread; total memory includes other overhead |
| `-m 2` | Up to two Bowtie1 mismatches; allowed range 0–3 |
| `-M 10000` | Per-position pileup depth cap; not guaranteed uniform random sampling |
| `--cutoff 3` | Use reads with at most three remaining A bases for the selected ratio |
| `--keep-tmp` | Retain site counts, alignment reports and other intermediate files |

Other parameters use the script defaults: minimum A+G coverage 15, minimum A count 5, minimum ratio 0.1, and raw/adjusted P-value thresholds of 0.005. List all options with `python /path/to/your/glori-amplicon/run_GLORI_amplicon.py --help`.

Do not increase `-m` based on the anticipated number of m6A sites: A bases in both reads and reference become G before alignment, so m6A sites do not themselves add A/G mismatches at this step.

Increasing `-T` does not accelerate Step 1. This version already writes Step 1 text in batches and uses the current `statsmodels.stats.multitest` FDR interface. No manual `sed` repair is needed.

If a command fails, inspect the error before continuing. For a rerun, choose a new output directory, such as `-o output_retry1`; do not mix inputs, parameters or incomplete runs in one output directory.

## 9. Check the results

```bash
samtools quickcheck output/sample1_r.sorted.bam
samtools view -c output/sample1_r.sorted.bam
samtools view -c -f 16 output/sample1_r.sorted.bam
cat output/tmp/sample1.sam.output
cat output/sample1.totalCR.txt
cat output/sample1.totalm6A.FDR.csv
```

| Check | Expected behavior |
|---|---|
| `samtools quickcheck` | No output on success; do not use a BAM that fails this check |
| `samtools view -c` | More than zero alignment records |
| `samtools view -c -f 16` | Zero for a successful run of this forward-only workflow |
| `sample1.sam.output` | Bowtie alignment statistics |
| `sample1.totalCR.txt` | Estimated background A→G conversion rates |
| `sample1.totalm6A.FDR.csv` | Sites passing candidate filters and FDR; header retained even if no site passes |

Key result columns:

| Column | Meaning |
|---|---|
| `Chr` / `Gene` | Your amplicon ID |
| `Sites` | Position in the original amplicon FASTA, starting at 1; not automatically converted to a genomic coordinate |
| `Strand` | Orientation relative to the reference |
| `AGcov` | A+G count at this position among the reads used |
| `Acov` | A count among those reads |
| `Ratio` | `Acov / AGcov`, the A-retention proportion under the selected filters |
| `CR` | Background conversion rate used by the program |
| `Pvalue` / `P_adjust` | Statistical-test and adjusted P values |

Despite its `.csv` extension, the file is **tab-separated**. Choose a tab delimiter when importing it into Excel.

A target absent from the final table must not automatically be recorded as zero. It may fail coverage, A-count, ratio, read-filter or statistical thresholds. With `--keep-tmp`, `output/tmp/sample1.totalformat.txt` retains counts for further inspection.

## 10. Process another sample and record settings

Create a separate working directory for each sample, such as `/path/to/your/analysis/sample2`, and repeat Steps 5–9. Update the input name, trimmed filename and `-pre`. Keep reference, adapter settings, filtering parameters and software versions consistent across a comparison where appropriate.

You do not need to recreate the environment. Save the environment list and commands in your private analysis directory for reproducibility; do not submit the complete analysis directory, with private paths or data, to a public code repository.

```bash
conda list --explicit > software_versions.txt
```

This records exact installed packages for the current platform. The file may include package-channel URLs; inspect it before sharing publicly.

When finished, run `exit` in the Slurm interactive shell to release resources. Prioritize downloading the site table, conversion rates, alignment statistics and FastQC HTML; you usually do not need all intermediate files locally.

## 11. Interpretation and limitations

- `Ratio` measures observed A retention under GLORI. It does not automatically correct incomplete conversion, amplification bias or all sequencing errors. Without UMIs, read counts are not independent RNA molecule counts.
- In a short amplicon, true retained-A sites can affect per-amplicon background estimates. Interpret results alongside unmethylated controls, positive controls and replicates; successful execution is not biological validation.
- `--cutoff 3` may also remove reads carrying several genuinely modified sites. Evaluate it against the design, rather than relaxing it merely to obtain a desired result.
- FDR follows the upstream logic and is calculated over prefiltered candidates, not uniformly over all reference A positions.
- Amplicons can become identical or difficult to distinguish after A→G conversion. Unique-alignment filtering may exclude their reads.
- Paired-end alignment, automatic UMI identification and reverse-read quantification are not supported. A reverse-alignment error requires checking library design, selected end and reference orientation.
- This workflow is not intended for clinical diagnosis without further validation.

## 12. Brief troubleshooting

| Symptom | Action |
|---|---|
| `command not found` / Python import error | Activate the correct environment and repeat Step 3 checks |
| Package-channel `Name or service not known` | Follow cluster DNS/proxy policies; a regional option is the [Tsinghua mirror guide](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/) for changing channel URLs in `environment.yml` |
| Nonempty output directory | Use a new `-o` directory to avoid stale results |
| Insufficient sort memory | Reduce `--sort-threads`, lower `--sort-memory` if necessary, and request more job memory; `-M` does not control sorting memory |
| No alignments or reverse-alignment error | Check read orientation, adapter trimming, reference and sample correspondence |
| Final table contains only column names | Execution may have completed with no passing sites; inspect counts and thresholds rather than interpreting all sites as zero |

## 13. Citation, license and contributions

Cite GLORI-tools, the original GLORI paper and the GLORI 3.0 paper/code record when that experimental method applies. Full entries are in [README: Citation and provenance](../README.md#citation-and-provenance). This adaptation contributes amplicon support, compatibility and robustness fixes, dependencies and documentation; it does not claim invention of GLORI or endorsement by its authors.

The original upstream MIT notices are retained in [LICENSES/](../LICENSES/); [LICENSE](../LICENSE) covers this adaptation's original contributions. See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for sources and changes. No paper PDF, figure, Zenodo companion script or study data is bundled.

For issue reports, include software versions, a command with private paths and data identifiers removed, the error text and failed step. Do not post confidential reads, reference sequences or credentials in a public issue.

Maintainers can run `python -m unittest discover -s tests -v` in the environment. Automated checks create only the minimal temporary inputs they need; they do not require study data or provide a downloadable biological validation dataset.
