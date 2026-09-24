# Contributing

This is an unofficial amplicon adaptation. Please preserve the original GLORI and RNA-m5C notices and distinguish engineering changes from changes to the scientific model.

For an issue, include your software versions, the failed step, the error text and a command with personal paths and identifiers replaced by placeholders. Do not post confidential reads, reference sequences, results, credentials or private cluster logs.

For a code change, explain the problem and resulting behavior. Run `python -m unittest discover -s tests -v` in the documented Linux Conda environment. Statistical changes need an explanation of their effect on counts, background estimation and filtering, together with a regression check. Passing tests does not establish biological validation.

Keep user-generated inputs and outputs outside the source directory. Tests may construct minimal inputs in temporary directories; do not add experimental or downloadable demonstration datasets. When changing an input contract or a command, update the English and Chinese guides and input requirements in `docs/`, plus `README.md` when the overview changes.
