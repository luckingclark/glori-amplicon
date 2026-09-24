"""Regression checks; any test reads are generated only in temporary directories.

Run from the repository root: python -m unittest discover -s tests -v
Full pipeline checks require Linux and the documented Conda environment.
"""

import csv
import importlib.util
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run_GLORI_amplicon as pipeline


class SafetyTests(unittest.TestCase):
    def test_refuse_existing_results_without_changing_them(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'analysis'
            pipeline.prepare_output_directory(str(path))
            marker = path / 'previous.result'
            marker.write_text('keep this')
            with self.assertRaisesRegex(ValueError, 'new or empty'):
                pipeline.prepare_output_directory(str(path))
            self.assertEqual(marker.read_text(), 'keep this')

    def test_subprocess_failure_propagates(self):
        with self.assertRaises(subprocess.CalledProcessError):
            pipeline.run_command([sys.executable, '-c', 'raise SystemExit(7)'])

    def test_reverse_alignment_stops_before_base_restoration(self):
        with tempfile.TemporaryDirectory() as temp:
            sam = Path(temp) / 'toy.sam'
            sam.write_text('@HD\tVN:1.0\nread1\t16\tAMP1\t1\t255\t4M\t*\t0\t0\tGCGT\tIIII\n')
            with self.assertRaisesRegex(ValueError, 'Reverse-strand'):
                pipeline.validate_alignment_orientation(str(sam))

    def test_unmapped_input_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            sam = Path(temp) / 'toy.sam'
            sam.write_text('read1\t4\t*\t0\t0\t*\t*\t0\t0\tGCGT\tIIII\n')
            with self.assertRaisesRegex(ValueError, 'No reads mapped'):
                pipeline.validate_alignment_orientation(str(sam))

    def test_conversion_preserves_quality_and_records_original_a_positions(self):
        with tempfile.TemporaryDirectory(prefix='glori test ') as temp:
            base = Path(temp)
            fastq = base / 'reads.fq'
            changed = base / 'changed.fq'
            bed = base / 'positions.bed'
            fastq.write_text('@read1 description\nACAGT\n+\nIIIII\n@read2\nGCGTT\n+\nIIIII\n')
            pipeline.change_reads(str(fastq), str(changed), str(bed), str(base), 'AG')
            self.assertEqual(changed.read_text(), '@read1\nGCGGT\n+\nIIIII\n@read2\nGCGTT\n+\nIIIII\n')
            self.assertEqual(Path(str(bed) + '_sorted').read_text(), 'read1\t0_2\nread2\tNA\n')

    def test_incomplete_fastq_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            fastq = base / 'reads.fq'
            fastq.write_text('@read1\nACGT\n+\n')
            with self.assertRaisesRegex(ValueError, 'Incomplete FASTQ'):
                pipeline.change_reads(str(fastq), str(base / 'changed.fq'),
                                      str(base / 'positions.bed'), str(base), 'AG')

    def test_duplicate_first_header_tokens_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            fastq = base / 'reads.fq'
            fastq.write_text('@read1 first description\nACGT\n+\nIIII\n'
                             '@read01\nGCGT\n+\nIIII\n'
                             '@read1 second description\nAAGT\n+\nIIII\n')
            with self.assertRaisesRegex(ValueError, 'Duplicate FASTQ read ID: read1'):
                pipeline.change_reads(str(fastq), str(base / 'changed.fq'),
                                      str(base / 'positions.bed'), str(base), 'AG')


HAS_STATSMODELS = importlib.util.find_spec('statsmodels') is not None


@unittest.skipUnless(HAS_STATSMODELS, 'statsmodels is required for FDR tests')
class FDRTests(unittest.TestCase):
    def run_filter(self, input_text):
        self.directory = tempfile.TemporaryDirectory(prefix='glori fdr ')
        self.addCleanup(self.directory.cleanup)
        base = Path(self.directory.name)
        source = base / 'candidates.txt'
        source.write_text(input_text)
        output = base / 'result'
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'pipelines' / 'm6A_caller_FDRfilter.py'),
             '-i', str(source), '-o', str(output)], capture_output=True, text=True)
        return completed, Path(str(output) + '.csv')

    def test_zero_candidates_has_header_and_is_successful(self):
        completed, output = self.run_filter('')
        self.assertEqual(completed.returncode, 0, completed.stderr)
        with output.open() as handle:
            table = csv.DictReader(handle, delimiter='\t')
            self.assertEqual(table.fieldnames, ['Chr', 'Sites', 'Strand', 'Gene', 'CR',
                                               'AGcov', 'Acov', 'Genecov', 'Ratio',
                                               'Pvalue', 'P_adjust'])
            self.assertEqual(list(table), [])

    def test_malformed_input_fails_instead_of_reporting_no_sites(self):
        completed, output = self.run_filter('AMP1\t48\t+\n')
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(output.exists())

    def test_candidate_that_fails_fdr_produces_header_only(self):
        fields = ['AMP1', '48', '+', 'AMP1', 'AMP1', 'AMP1', 'NA', 'amplicon',
                  '0.05', '100', '100', '100', '10', '0.1', '0.5', '1', '100', '1']
        completed, output = self.run_filter('\t'.join(fields) + '\n')
        self.assertEqual(completed.returncode, 0, completed.stderr)
        with output.open() as handle:
            self.assertEqual(list(csv.DictReader(handle, delimiter='\t')), [])


@unittest.skipUnless(HAS_STATSMODELS, 'statsmodels is required for statistical stage tests')
class CallingStageTests(unittest.TestCase):
    def test_known_counts_and_zero_candidate_output(self):
        with tempfile.TemporaryDirectory(prefix='glori calls ') as temp:
            base = Path(temp)
            mpi = base / 'toy.mpi'
            anno = base / 'toy.baseanno'
            positions = list(range(1, 20)) + [48]
            with mpi.open('w') as pileup, anno.open('w') as annotation:
                for position in positions:
                    bases = ['A'] * 95 + ['G'] * 5 if position == 48 else ['G'] * 100
                    pileup.write('\t'.join(['AMP1_AG_converted', str(position), '+', 'A',
                                            ','.join(bases), ','.join(['1'] * 95 + ['0'] * 5)]) + '\n')
                    annotation.write('\t'.join(['AMP1', str(position - 1), str(position), '+',
                                                'AMP1', 'AMP1', 'AMP1', 'NA', 'amplicon']) + '\n')
            def run(helper, arguments):
                completed = subprocess.run([sys.executable, str(ROOT / 'pipelines' / helper)]
                                           + [str(arg) for arg in arguments], capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            formatted = base / 'formatted.txt'
            run('m6A_pileup_formatter.py', ['-i', mpi, '--db', anno, '-o', formatted,
                                           '--CR', base / 'CR.txt'])
            run('m6A_caller.py', ['-i', formatted, '-o', base / 'calls', '--cutoff', '3'])
            run('m6A_caller_FDRfilter.py', ['-i', base / 'calls.3.txt', '-o', base / 'result'])
            with (base / 'result.csv').open() as handle:
                rows = list(csv.DictReader(handle, delimiter='\t'))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['Sites'], '48')
            self.assertEqual(int(rows[0]['AGcov']), 100)
            self.assertEqual(int(rows[0]['Acov']), 95)
            self.assertAlmostEqual(float(rows[0]['Ratio']), 0.95)
            self.assertAlmostEqual(float(rows[0]['CR']), 0.9525)
            run('m6A_caller.py', ['-i', formatted, '-o', base / 'no_calls', '--cutoff', '3', '-C', '101'])
            self.assertEqual((base / 'no_calls.3.txt').stat().st_size, 0)
            run('m6A_caller_FDRfilter.py', ['-i', base / 'no_calls.3.txt', '-o', base / 'empty'])
            with (base / 'empty.csv').open() as handle:
                self.assertEqual(list(csv.DictReader(handle, delimiter='\t')), [])


HAS_PIPELINE = (sys.platform.startswith('linux') and HAS_STATSMODELS
                and importlib.util.find_spec('pysam') is not None
                and all(shutil.which(tool) for tool in ['bowtie', 'bowtie-build', 'samtools']))


@unittest.skipUnless(HAS_PIPELINE, 'Linux plus full Conda dependencies required for pipeline tests')
class PipelineTests(unittest.TestCase):
    def test_positive_and_zero_candidate_runs_and_output_reuse_guard(self):
        # No experimental sequences or read headers are used in this test.
        with tempfile.TemporaryDirectory(prefix='glori smoke ') as temp:
            base = Path(temp)
            rng = random.Random(2026)
            sequence = list(''.join(rng.choices('ACGT', k=100)))
            sequence[47] = 'A'
            sequence = ''.join(sequence)
            reference = base / 'amplicons.fa'
            # An ID containing GL must obey the same user-requested depth as any other ID.
            reference.write_text('>GL_AMP1\n' + sequence + '\n')
            reads = base / 'reads.fq'
            converted = sequence.replace('A', 'G')
            with reads.open('w') as output:
                for index in range(2000):
                    read = list(converted)
                    if index < 1900:
                        read[47] = 'A'
                    output.write(f'@read{index:04d}\n{"".join(read)}\n+\n{"I" * 100}\n')
            env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
            def run(arguments):
                return subprocess.run([sys.executable] + [str(x) for x in arguments],
                                      capture_output=True, text=True, env=env)
            prepared = run([ROOT / 'prepare_amplicon_ref.py', '-f', reference,
                            '-o', base / 'ref', '-pre', 'panel', '-p', '1'])
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            self.assertTrue(Path(str(reference) + '.fai').exists())
            common = [ROOT / 'run_GLORI_amplicon.py', '-q', reads,
                      '-f', base / 'ref' / 'panel.AG_conversion.fa', '-f2', reference,
                      '-b', base / 'ref' / 'panel.baseanno', '-pre', 'toy',
                      '-T', '1', '--sort-threads', '1', '--keep-tmp']
            positive_args = common + ['-o', base / 'positive']
            positive = run(positive_args)
            self.assertEqual(positive.returncode, 0, positive.stdout + positive.stderr)
            with (base / 'positive' / 'toy.totalm6A.FDR.csv').open() as handle:
                rows = list(csv.DictReader(handle, delimiter='\t'))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['Sites'], '48')
            self.assertEqual(int(rows[0]['AGcov']), 2000)
            self.assertEqual(int(rows[0]['Acov']), 1900)
            self.assertAlmostEqual(float(rows[0]['Ratio']), 0.95)
            depth_capped = run(common + ['-o', base / 'depth_capped', '-M', '500'])
            self.assertEqual(depth_capped.returncode, 0, depth_capped.stdout + depth_capped.stderr)
            with (base / 'depth_capped' / 'toy.totalm6A.FDR.csv').open() as handle:
                capped_rows = list(csv.DictReader(handle, delimiter='\t'))
            self.assertEqual(len(capped_rows), 1)
            self.assertEqual(int(capped_rows[0]['AGcov']), 500)
            repeat = run(positive_args)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertIn('new or empty', repeat.stderr)
            no_sites = run(common + ['-o', base / 'empty', '-C', '3000'])
            self.assertEqual(no_sites.returncode, 0, no_sites.stdout + no_sites.stderr)
            with (base / 'empty' / 'toy.totalm6A.FDR.csv').open() as handle:
                self.assertEqual(list(csv.DictReader(handle, delimiter='\t')), [])


if __name__ == '__main__':
    unittest.main()
