# Contributing to crimm-dock

For everyone who changes this repository, human or AI. AI agents get their working
instructions from [AGENTS.md](AGENTS.md); the rules here bind them too.

## Set up

The development environment is crimm's, `crimm-dev`, plus FFTW3F and an OpenMP-capable
compiler for the C extension:

```bash
conda activate crimm-dev
conda install fftw   # provides libfftw3f / libfftw3f_threads
pip install -e . --no-deps
```

`setup.py` builds `crimm_dock.fft_docking` from `src/fft_docking/*.c` against
`$CONDA_PREFIX/include` and `$CONDA_PREFIX/lib`, linking `fftw3f`, `fftw3f_threads` and an
OpenMP runtime (`gomp`/`iomp5`/`omp` depending on `$CC`). The compiled extension is
version- and platform-specific (`cpython-<version>-<arch>.so`); rebuild it for every Python
you run against. Check with:

```bash
python -B -c "import crimm_dock; print(crimm_dock.__file__)"
```

## Run the tests

There is no real automated test suite yet (`docs/dev/NOTES.md` has the detail: `tests/`
currently holds ad-hoc exploration scripts, not pytest tests). Building one is the top
priority in `docs/dev/ROADMAP.md`. Until it exists, verify a change by running the smallest
reproduction script that exercises it and reporting the numbers, the same way a bug report
should.

## Changing code

- One concern per commit and per pull request. A fix does not ride along with a rename.
- Say in a docstring whether a function modifies its argument, and give units for any
  physical quantity (Å, e, kcal/mol).
- A change to the vdW/electrostatic grid formulas, the mixing rule, or anything that changes
  docking energies or poses is a **correctness** change: describe the before/after numerically
  in the pull request, not just "refactor".
- Run output and generated `.dx`/pose files are never committed.
- A `TODO` in code carries an issue number.

## Issues and pull requests

- Work is tracked as GitHub issues at https://github.com/Truman-Xu/crimm-dock/issues. Use the
  issue forms.
- Open a pull request from a short-lived branch, with a description of why the change is
  made. Squash-merge; delete the branch after.
- A commit that **finishes** an issue ends its message with `Closes #N` on its own line,
  above the `Co-Authored-By` trailer. A commit that only works toward an issue says `Part of
  #N`.
- A correctness bug (wrong docking energies, grids, or poses) blocks use of the affected
  release.

## Credit and authorship

- Every commit carries its authors. An AI model that wrote a substantial part signs with a
  trailer naming the exact model: `Co-Authored-By: <model name and version> <vendor
  no-reply address>`.
- Source files carry no signatures: no author lines, "generated with" banners, model names or
  session notes in code, comments, docstrings or file names. `git log` and `git blame` are
  the record.
- This project reimplements CHARMM's FASTDOCK/CDOCKER method, read from the licensed CHARMM
  source under permission from Prof. Charles Brooks. Do not paste CHARMM source into this
  repository, issues, or commit messages; cite the method and the papers in `papers/`
  (git-ignored) instead.
- Never remove or rewrite someone else's credit.
