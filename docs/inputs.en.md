# Input requirements

[Chinese version](inputs.zh-CN.md) | [User guide](usage.en.md) | [Repository overview](../README.md)

## Two required inputs

| File | Content and source |
|---|---|
| `sample1_R1.fq.gz` | Demultiplexed reads and qualities from your sequencing provider; one sample and one selected read end per run |
| `amplicons.fa` | One or more confirmed, complete target amplicon sequences, preserving original A bases, from the original transcript or construct design; not merely two primers |

Names are placeholders. Run samples separately; identical designs may share a reference. A whole genome, GTF, STAR index, spreadsheet sample sheet or manually written annotation is not needed.

## FASTQ

- Each read has four lines: `@name`, sequence, a separator starting with `+`, and quality characters. Sequence and quality lengths must match and must not wrap. Use Phred+33 quality encoding.
- Read names before the first whitespace must be unique across the file. Keep the platform's original names; do not edit FASTQ in Word or Excel.
- Supported extensions are `.fq`, `.fastq`, `.fq.gz` and `.fastq.gz`. Gzip files must end in lowercase `.gz`; renaming does not compress or decompress them.
- Select the end matching the original RNA-oriented forward reference for A→G analysis. R1 is not universally appropriate. Do not combine R1/R2 or different samples. Merging lanes of one sample still requires the same read end and unique read IDs.
- The guide trims sequencing adapters before passing cleaned reads to the main program. i5/i7 are sample indexes, not molecular UMIs. The direct workflow assumes no molecular UMI; preprocess any UMI/inline barcode according to the actual library design. Do not deduplicate non-UMI amplicons solely by sequence or coordinates.

## Original amplicon FASTA

Save plain text, with each record starting with `>amplicon_ID`, followed by your actual complete sequence. Proper FASTA line wrapping is allowed. No placeholder bases or example dataset are supplied.

| Item | Requirement |
|---|---|
| Format | Uncompressed `.fa` / `.fasta`; the reference script does not directly read `.fa.gz` |
| Orientation and source | Original RNA 5′→3′ orientation, correct transcript/splice form or actual construct; not a consensus of converted reads |
| Bases | `A/C/G/T/N`, using T for U; every record must retain at least one original A, before A→G conversion; uppercase is recommended |
| ID | Unique and short; start with a letter/digit, followed only by letters, digits, `_ . -`; no spaces or `_AG_converted` |
| Boundaries | Match the target fragment remaining after sequencing-adapter trimming; exclude sequencing adapters, i5/i7 indexes and unrelated vector sequence |
| Permissions | The reference directory must be writable to create the adjacent `.fai` |

`N` is not a quantifiable A and can reduce alignment coverage; resolve the actual base where possible. Do not substitute an intron-containing genomic fragment for a mature RNA reference.

Sequencing adapters and PCR primers are different: standard adapter trimming does not identify gene-specific primers automatically. Reference and read processing must agree; do not remove only the reference ends while retaining their counterparts in reads. Quantified sites should be outside regions whose bases are directly supplied by PCR primers; the program does not mask those regions automatically.

If amplicons become identical or highly similar after A→G conversion, unique-alignment filtering may exclude their reads. Changing IDs does not resolve sequence ambiguity.

## Design information and automatically generated files

Check the sample, read orientation, adapter type, UMI status, amplicon/primer boundaries, controls and replicates against experimental records. Target positions use 1-based coordinates on the original FASTA. No additional primer file or target BED is required.

| Generated file | Source / purpose |
|---|---|
| Trimmed `.fq` | Trim Galore output, passed to the main program with `-q` |
| `panel.AG_conversion.fa` | Reference-builder output, passed with `-f` |
| Six `.ebwt` files and two `.fai` files | Automatically generated Bowtie1 / FASTA indexes |
| `panel.baseanno` | Automatically generated site annotation, passed with `-b` |
| BAM, conversion rates and site table | Main-program outputs |

`-f2` takes the original unconverted FASTA; do not swap it with `-f`. Rebuild all indexes after changing reference sequences or IDs.

## Before running

Activate the environment and replace the paths, then run:

```bash
ls -lh /path/to/your/data/sample1_R1.fq.gz /path/to/your/data/amplicons.fa
gzip -t /path/to/your/data/sample1_R1.fq.gz
seqkit stats /path/to/your/data/sample1_R1.fq.gz /path/to/your/data/amplicons.fa
cat /path/to/your/data/amplicons.fa
```

These check existence/size, gzip integrity, counts/lengths and actual reference content. Files should be nonempty. `gzip -t` is silent on success; skip it for uncompressed FASTQ. These checks do not establish experimental correctness. Continue with the [user guide](usage.en.md).
