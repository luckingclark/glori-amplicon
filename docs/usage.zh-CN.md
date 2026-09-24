# GLORI Amplicon 操作指南

[English](usage.en.md) | [仓库首页](../README.md) | [输入文件规范](inputs.zh-CN.md)

An unofficial amplicon adaptation of [GLORI-tools](https://github.com/liucongcas/GLORI-tools). The GLORI algorithms and experimental methods belong to their original authors. This repository provides an amplicon reference builder, an adapted analysis entry point, dependency configuration and a step-by-step guide. It is not an official GLORI release or a new m6A detection method.

本项目基于 GLORI-tools 代码改编，并参考 [GLORI 3.0 配套代码](https://doi.org/10.5281/zenodo.14233421)及 [GLORI 3.0 论文](https://doi.org/10.1038/s41592-025-02680-9)的方法。适合使用少量自定义扩增子参考的单端 GLORI 数据。代码来源、许可证边界和完整引用分别见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) 和 [CITATIONS.md](../CITATIONS.md)。

**仓库不提供实验数据、人工合成示例数据、参考序列或结果表。** 以下流程使用你自己的 FASTQ 和 FASTA。`sample1` 仅是输出名称占位符，不代表真实样品。

首次使用请先看 [输入文件规范 inputs.zh-CN.md](inputs.zh-CN.md)：需要自行提供一份样品的选定读端 FASTQ，以及原始扩增子 FASTA；该页逐项解释文件内容、格式、方向、引物区和由程序生成的文件。

## 1．适用范围与分析流程

```text
你的单端 FASTQ
  → Trim Galore 去测序接头及低质量末端
  → 使用原始扩增子 FASTA 建立 A→G 参考及索引
  → reads A→G 转换、Bowtie1 比对、恢复 read 中的 A
  → pileup、位点计数、背景检验及 FDR 校正
  → 结果表、转化率和 BAM
```

运行环境是 **Linux、Bash、Conda**，可在 Slurm 集群上使用。Windows 可以用来下载代码和传输文件；不要把下面的 Bash 命令直接粘贴到 Windows PowerShell。

本教程的直接流程针对**没有分子 UMI**的文库。i5/i7 样品 index 不等于分子 UMI。若文库有分子 UMI，需要先根据真实建库结构完成相应处理；本程序不自动识别或去除 UMI。对无 UMI 的短扩增子，不要直接按全序列或比对坐标去重。

只选择一个读端，且其方向应与原始 RNA / FASTA 正向一致，呈现 A→G 转换。双端下机数据可以只使用符合这个要求的一端。下文文件名写作 `sample1_R1.fq.gz`，但 **R1 并非适用于所有建库方式**。程序遇到反向比对会停止，避免输出未经支持的定量结果。

不需要人或小鼠全基因组、STAR 索引、全基因组 GTF，也不需要 R。

## 2．下载代码，明确三个目录

在本仓库 GitHub 页面选择 **Code → Download ZIP**，解压后将整个代码文件夹传到 Linux。也可以通过 Git 克隆仓库，但不要求新手先学习 Git。

以下路径全部是占位符。**执行前必须替换成你自己的真实路径**；不要在系统根目录真的创建一个名为 `path/to/your` 的文件夹。

| 本文写法 | 替换成什么 |
|---|---|
| `/path/to/your/glori-amplicon` | 解压后的代码目录，里面直接包含 README.md 和两个主程序 |
| `/path/to/your/data` | 你存放原始 FASTQ 和扩增子 FASTA 的目录 |
| `/path/to/your/analysis/sample1` | 本次样品的工作目录，清洗文件、索引和结果会写在这里 |
| `/path/to/your/miniforge3` | 仅在需要初始化 Conda 时使用，替换为你的 Conda 安装目录 |

文件路径建议用英文、数字、下划线和连字符。输入与输出可以放在不同磁盘，但必须有读取输入、写入工作目录的权限，并为解压文件、SAM、BAM 和中间文件预留空间。

代码目录应至少包含：

```text
glori-amplicon/
├── README.md
├── docs/  # 中英文操作指南与输入规范
├── environment.yml
├── LICENSE
├── LICENSES/
├── CITATIONS.md
├── THIRD_PARTY_NOTICES.md
├── prepare_amplicon_ref.py
├── run_GLORI_amplicon.py
├── pipelines/
└── tests/
```

## 3．建立 Conda 环境——首次使用时执行一次

集群如果已有 Conda，先按集群说明加载它，然后检查：

```bash
conda --version
```

应显示 Conda 版本。如果提示找不到命令，需要先加载本集群的 Conda 模块，或安装 [Miniforge](https://github.com/conda-forge/miniforge)。这取决于你的集群配置，本项目不会假定管理员的安装路径。

进入代码目录并创建环境：

```bash
cd /path/to/your/glori-amplicon
export CONDA_CHANNEL_PRIORITY=strict
conda env create --file environment.yml
conda activate glori_amplicon
```

| 命令 | 作用 |
|---|---|
| `cd ...` | 进入代码所在文件夹 |
| `export CONDA_CHANNEL_PRIORITY=strict` | 在当前终端设置软件源的严格优先级 |
| `conda env create --file environment.yml` | 按仓库的依赖文件建立环境，名称是 `glori_amplicon` |
| `conda activate glori_amplicon` | 使用这个环境中的软件；提示符通常会出现 `(glori_amplicon)` |

这里使用环境名称，不依赖项目路径变量。`environment.yml` 中没有个人的 `prefix` 或绝对安装路径。它是用于创建环境的依赖配置，不是每个平台完全相同的构建锁文件。

| 环境中的软件 | 用途 |
|---|---|
| Python 3.10、biopython、pysam | 运行 Python 脚本并读写序列、比对文件 |
| numpy、pandas、scipy、statsmodels | 数值处理、结果表和统计检验 |
| Bowtie 1.3.1 | 扩增子比对，不能替换成 Bowtie2 |
| samtools | 参考索引、BAM 排序与检查 |
| Trim Galore 0.6.10、Cutadapt 4.x | 接头和质量修剪 |
| SeqKit、FastQC | FASTQ 数量、长度统计与质量报告 |

如果环境名称已经存在，先尝试激活和检查，不要删除旧环境。也可用 `conda env create --name your_glori_env --file environment.yml` 创建另一个名字，之后对应改用 `conda activate your_glori_env`。

检查安装：

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

第一条应显示 `Python dependencies OK`，其余应显示软件版本或帮助。如果报错，先解决安装问题再处理数据。

重新登录后通常只需要 `conda activate glori_amplicon`。如果提示终端尚未初始化，可以按实际安装位置执行：

```bash
source /path/to/your/miniforge3/etc/profile.d/conda.sh
conda activate glori_amplicon
```

## 4．在集群申请计算资源

在普通 Linux 工作站运行时可以跳过本小节。在 Slurm 集群中，数据处理应在分配到的计算节点上运行；下面在登录节点申请一个交互终端：

```bash
srun --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=16G --time=08:00:00 --pty bash
```

这表示申请 1 个节点、1 个任务、8 个 CPU 核、16 GB 内存、最长 8 小时。实际分区、账户和资源限制以你所在集群为准。如果要求分区，在命令里添加 `--partition=你的实际分区名`；可用 `sinfo -s` 查看。已经在计算节点中时，不要重复申请。

进入计算节点后，激活环境并限制数学库额外线程：

```bash
conda activate glori_amplicon
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
```

如果 `conda activate` 在新终端不可用，先执行上一节的 `source` 命令。最后一行限制每个数学库额外启动的线程，避免多个进程同时占用过多 CPU。

交互计算期间保持连接。长任务如需断线继续，应按所在集群的说明改用批处理；不要在登录节点后台直接运行大型分析。

## 5．准备你的 FASTQ 和原始扩增子参考

详细格式、来源和准备规则见 [inputs.zh-CN.md](inputs.zh-CN.md)。以下概述与后续命令一一对应。

准备以下两个输入，名称可以不同，后续命令要相应修改：

| 文件 | 要求 |
|---|---|
| `/path/to/your/data/sample1_R1.fq.gz` | 一个样品选定读端的 FASTQ，标准每条四行、Phred+33 质量编码、read ID 唯一；已按样品拆分 |
| `/path/to/your/data/amplicons.fa` | 未压缩、未做 A→G 转换的扩增子参考 FASTA，可以包含一个或多个扩增子；不能只写两条引物 |

FASTA 中每条序列第一行以 `>` 开头，后面是你自己的扩增子 ID；接下来的行是实际序列。参考必须来自已知的原始序列，**原本的 A 要保留**，不能用已发生 GLORI 转换的 read 共识替代。

参考按原始 RNA 的 5′→3′方向，使用 DNA 字母 `A/C/G/T`，RNA 中的 U 写成 T。程序允许 `N`，但未知碱基会影响比对，不是可定量的 A 位点；不接受其他模糊字母。每条参考至少含一个原始 A。ID 不要重复、不要有空格；首字符为英文字母或数字，其余可用英文字母、数字、下划线、点或连字符，任何位置均不能包含保留标记 `_AG_converted`。

参考应对应去测序接头后要比对的目标片段，不包含测序 adapter。目标定量位点应避开 PCR 引物直接覆盖、写入的区域；本程序不自动推断目标引物位置，也不自动区分引物带来的碱基和模板碱基。

建立本次工作的目录：

```bash
mkdir -p /path/to/your/analysis/sample1
cd /path/to/your/analysis/sample1
mkdir -p trimmed qc
cp /path/to/your/data/amplicons.fa reference.fa
```

`mkdir -p` 建立目录；`cd` 进入目录；`cp` 将你的参考复制到当前目录，后面统一叫 `reference.fa`。原始 FASTQ 不需要复制或提前手动解压。

检查输入：

```bash
gzip -t /path/to/your/data/sample1_R1.fq.gz
seqkit stats /path/to/your/data/sample1_R1.fq.gz
cat reference.fa
```

`gzip -t` 成功时通常没有输出，表示压缩文件能正常读取。`seqkit stats` 显示序列数量和长度，`num_seqs` 不应为 0。`cat` 显示参考内容，检查它确实是自己的目标片段。

## 6．去测序接头和低质量末端

下面适用于标准 Illumina 接头；文库使用其他接头时，应按实际建库方案修改接头参数，不要盲目使用此设置。

```bash
trim_galore --illumina -q 20 --stringency 5 -e 0.1 --length 25 --dont_gzip -o trimmed /path/to/your/data/sample1_R1.fq.gz
```

| 参数 | 含义 |
|---|---|
| `--illumina` | 识别标准 Illumina 接头 `AGATCGGAAGAGC` |
| `-q 20` | 使用 Phred 20 进行质量修剪 |
| `--stringency 5` | 接头匹配至少重叠 5 个碱基 |
| `-e 0.1` | 接头匹配允许的错误比例为 0.1 |
| `--length 25` | 丢弃修剪后不足 25 nt 的 reads；若目标更短，需要另行评估参数 |
| `--dont_gzip` | 输出普通 `.fq` 文件 |
| `-o trimmed` | 输出到当前工作目录的 `trimmed` 中 |

这里只用一端，所以没有 `--paired`。如果输入文件是 `sample1_R1.fq.gz`，输出应为 `trimmed/sample1_R1_trimmed.fq`；如果输入名称不同，清洗文件名也会对应改变。

```bash
seqkit stats trimmed/sample1_R1_trimmed.fq
fastqc -t 2 -o qc trimmed/sample1_R1_trimmed.fq
```

第一条查看清洗后的数量和长度。第二条生成 FastQC HTML 报告，可下载到本地浏览器查看。扩增子数据集中覆盖相同片段，高重复度和特殊碱基组成并不自动意味着失败；不要为消除这些报告警告而按序列去重。

## 7．准备 A→G 参考和索引

保持在 `/path/to/your/analysis/sample1` 中执行：

```bash
python /path/to/your/glori-amplicon/prepare_amplicon_ref.py -f reference.fa -pre panel -o ref -p 4
```

| 参数 | 含义 |
|---|---|
| `-f reference.fa` | 你的未转换参考 |
| `-pre panel` | 生成参考文件的前缀；不需要与样品名称相同 |
| `-o ref` | 保存生成的参考和索引 |
| `-p 4` | Bowtie 建索引使用 4 个线程 |

程序生成 `ref/panel.AG_conversion.fa`、6 个 `.ebwt` Bowtie 索引文件及 `ref/panel.baseanno`；还会为原始与转换参考生成 `.fai` 索引，因此原始参考所在目录必须可写。

```bash
ls ref
```

确认上述文件存在。原始 `reference.fa` 中的 A 不会被改掉；A→G 转换结果保存为另一份文件。

## 8．运行 GLORI amplicon 分析

```bash
python /path/to/your/glori-amplicon/run_GLORI_amplicon.py -q trimmed/sample1_R1_trimmed.fq -f ref/panel.AG_conversion.fa -f2 reference.fa -b ref/panel.baseanno -pre sample1 -o output -T 4 --sort-threads 2 --sort-memory 256M -m 2 -M 10000 --cutoff 3 --keep-tmp
```

代码会自动找到同目录的 `pipelines`，不要求你设置 `$PROJECT`、`PYTHONPATH` 或编辑脚本中的安装位置。

| 参数 | 含义 |
|---|---|
| `-q` | 清洗后的 FASTQ |
| `-f` | A→G 转换参考，用于比对 |
| `-f2` | 原始参考，用于确定哪些位置原本是 A |
| `-b` | 扩增子位点注释，启用按扩增子计算背景 |
| `-pre sample1` | 输出文件的前缀 |
| `-o output` | 本次结果目录，必须不存在或为空 |
| `-T 4` | 比对及部分后续处理的线程/进程数；第 1 步仍为单进程 |
| `--sort-threads 2` | 设置 samtools 排序的额外线程数，另有主线程；避免随 `-T` 一起增大 |
| `--sort-memory 256M` | 每个排序线程的近似内存设置，总进程内存还包含其他开销 |
| `-m 2` | Bowtie1 允许最多 2 个错配，合法范围是 0–3 |
| `-M 10000` | pileup 每位置的深度限制，不是保证均匀随机抽样 |
| `--cutoff 3` | 只用 read 中剩余 A 数不超过 3 的 reads 计算所选比例 |
| `--keep-tmp` | 保留位点计数、比对报告等中间文件，以便核查 |

其余参数采用脚本默认值：A+G 覆盖至少 15、A 计数至少 5、比例至少 0.1、原始 P 值和校正后 P 值阈值均为 0.005。所有参数可通过 `python /path/to/your/glori-amplicon/run_GLORI_amplicon.py --help` 查看。

不要根据预期 m6A 个数增大 `-m`：比对前 reads 与参考中的 A 都转换成 G，m6A 位点本身不会在此步骤增加 A/G 错配。

增加 `-T` 不能加速第 1 步。本版本已把第 1 步的字符串输出改为整批写入；FDR 使用当前的 `statsmodels.stats.multitest` 接口。相关修正已在脚本中完成，无需再手动运行 `sed` 修补。

命令失败时先阅读错误，不要继续下一步。重新运行请使用新的输出名，例如将 `-o output` 改成 `-o output_retry1`；不要把不同输入、参数或未完成的运行混在同一目录。

## 9．检查分析结果

```bash
samtools quickcheck output/sample1_r.sorted.bam
samtools view -c output/sample1_r.sorted.bam
samtools view -c -f 16 output/sample1_r.sorted.bam
cat output/tmp/sample1.sam.output
cat output/sample1.totalCR.txt
cat output/sample1.totalm6A.FDR.csv
```

| 检查 | 预期 |
|---|---|
| `samtools quickcheck` | 正常时没有输出；报错时不要使用该 BAM |
| `samtools view -c` | 比对记录数大于 0 |
| `samtools view -c -f 16` | 本流程成功运行时应为 0，表示没有未经支持的反向比对 |
| `sample1.sam.output` | Bowtie 原始比对统计 |
| `sample1.totalCR.txt` | 程序估计的背景 A→G 转化率 |
| `sample1.totalm6A.FDR.csv` | 通过候选筛选和 FDR 的位点表；没有通过位点时仍应保留表头 |

关键结果表列：

| 列 | 含义 |
|---|---|
| `Chr` / `Gene` | 你的扩增子 ID |
| `Sites` | 在原始扩增子 FASTA 上的位置，从 1 开始计数；不是自动换算后的基因组坐标 |
| `Strand` | 相对于参考的方向 |
| `AGcov` | 所用 reads 在该位置的 A+G 计数 |
| `Acov` | 其中 A 的计数 |
| `Ratio` | `Acov / AGcov`，即当前过滤条件下的 A 保留比例 |
| `CR` | 程序使用的背景转化率 |
| `Pvalue` / `P_adjust` | 统计检验及多重检验校正后的 P 值 |

虽然扩展名是 `.csv`，文件实际使用 **Tab（制表符）** 分隔。用 Excel 导入时选择制表符。

目标位点没有出现在最终表里，不能直接填成 0：它可能因覆盖、A 数、比例、read 过滤或统计阈值而未报告。`--keep-tmp` 会保留 `output/tmp/sample1.totalformat.txt`，可以进一步核查位点计数。

## 10．分析下一个样品，保存分析设置

为每个样品创建自己的工作目录，例如 `/path/to/your/analysis/sample2`，重复第 5–9 步。对应修改输入文件名、清洗文件名和 `-pre`。同一次比较尽量保持参考、接头设置、过滤参数和软件版本一致。

不需要重新创建 Conda 环境。可以将当前环境清单和运行命令保存在自己的分析目录，便于复现，但不应把包含私人路径或数据的完整分析目录提交到公共代码仓库。

```bash
conda list --explicit > software_versions.txt
```

这条命令把当前平台的精确安装列表写到 `software_versions.txt`。它是你的运行记录，可能包含软件源地址，不要未经检查直接公开。

分析结束后，在 Slurm 交互终端执行 `exit` 释放资源。下载结果时优先下载候选位点表、转化率、比对统计和 FastQC HTML，不必把整个中间文件目录搬回本地。

## 11．结果解释与当前限制

- `Ratio` 是 GLORI 的 A 保留观测指标，没有自动校正转化不足、扩增偏差或所有测序错误。无 UMI 时，reads 数不等于独立 RNA 分子数。
- 扩增子较短时，真实保留 A 位点也会影响按扩增子估计的背景。实验解释应结合未甲基化对照、阳性对照及重复；软件跑完不等于完成生物学验证。
- `--cutoff 3` 也可能过滤含多个真实修饰位点的 reads。阈值需要结合设计评估，不应仅为了得到想要的结果而放宽。
- FDR 继承上游逻辑，在经过预筛选的候选位点上计算，不应描述为对所有参考 A 位点进行的统一全局 FDR。
- 多个扩增子 A→G 转换后可能变得相同或难以区分；本流程沿用唯一比对筛选，相关 reads 可能被排除。
- 当前不提供成对比对、自动 UMI 识别或反向 reads 定量支持。遇到反向比对错误应先确认建库、所选读端和参考方向。
- 未经额外验证，不用于临床诊断。

## 12．简短故障处理

| 提示 | 处理 |
|---|---|
| `command not found` / Python 包导入错误 | 激活正确环境，重新检查第 3 步的软件和帮助输出 |
| 软件源 `Name or service not known` | 按集群联网要求处理 DNS/代理；国内可参考[清华镜像说明](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/)调整 `environment.yml` 的频道地址 |
| 输出目录非空 | 使用新的 `-o` 目录名，避免读取旧文件 |
| 排序内存不足 | 降低 `--sort-threads`，必要时降低 `--sort-memory` 并申请更多作业内存；`-M` 不控制排序内存 |
| 无比对或反向比对错误 | 检查读端方向、接头修剪、参考序列和对应样品 |
| 最终表只有列名 | 流程可以是正常完成，但无位点通过当前筛选；检查计数与阈值，不能解释成全部为零 |

## 13．引用、许可证与贡献

使用本项目分析数据时，请引用 GLORI-tools、原始 GLORI 论文及与你实验实际使用的方法相对应的 GLORI 3.0 论文/代码记录；完整条目见 [CITATIONS.md](../CITATIONS.md)。本项目的贡献是扩增子适配、兼容与稳健性修正、环境配置和操作文档，不声称发明 GLORI 算法或取得原作者背书。

GLORI-tools 的 MIT 版权及许可全文保留在 [LICENSE](../LICENSE)；相关来源、修改范围和未捆绑的第三方资料见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。本仓库不附带论文 PDF、图版、Zenodo 配套脚本或研究数据。

反馈问题时，请提供软件版本、去掉私人路径和数据标识的命令、错误文本以及发生在哪一步。不要把保密 FASTQ、参考序列或凭据直接贴到公开 issue。

维护者可在环境中运行 `python -m unittest discover -s tests -v` 检查代码。自动化测试只在临时目录构造必要的最小输入，不需要用户上传研究数据，也不提供用于生物学验证的示例数据包。
