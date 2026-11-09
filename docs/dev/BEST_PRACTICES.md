# Good practices for crimm-dock

Standards for keeping crimm-dock correct and maintainable. Targets, not a description of the
current state — `docs/dev/AGENT_HANDOFF.md` has the state.

## The short list

1. Every bug fix comes with a test that fails without it, once the test suite exists
   (`docs/dev/ROADMAP.md`, "Now"). Until then, a bug fix comes with a reproduction script and
   the before/after numbers in the pull request.
2. A change to grid formulas, the mixing rule, padding, or anything that changes docking
   energies or poses is a **correctness** change: say so explicitly and show numbers, not
   just "refactor" or "cleanup".
3. Single precision (`float32`) end to end in the numeric path; don't widen silently.
4. Units and in-place-or-not go in every docstring that touches physical quantities
   (Å, e, kcal/mol) or mutable arrays.
5. A `TODO` in the code points to an issue.
6. No direct pushes to `main`; changes arrive by pull request.
7. CHARMM source read under Prof. Brooks's permission never appears in this repository,
   issues, or commit messages — cite file/line/method name instead.

## Code

- Type-hint public functions where practical; this codebase currently doesn't, so match the
  surrounding style rather than mixing conventions file-by-file without a planned cleanup.
- Never catch bare `Exception` without re-raising or logging what was caught.
- Give a physical constant or magic number a named reference to its source (the paper, the
  CHARMM source file/line, or a CHARMM force-field parameter) instead of a bare literal.
- Prefer extending the C extension's existing function shapes (see `docs/dev/NOTES.md`) over
  adding a second ad-hoc path for the same calculation.

## Science-specific code

- Cite the method next to the implementation: FASTDOCK, CDOCKER, the specific CHARMM source
  file and routine being reimplemented (without quoting its text).
- Any mixing rule, cutoff, or softcore formula changed from the CHARMM reference must say so
  explicitly in a comment and in `docs/dev/NOTES.md`, with the reason (the geometric-mean vdW
  mixing rule is the existing example).
- Validate new grid math against the smallest possible case (one receptor atom, one probe
  atom, known distance) before trusting it on a real structure.
- Compare floats with tolerances chosen for the quantity; energies in kcal/mol, coordinates
  in Å.

## Testing

There is no suite yet; this is the standard to build toward (`docs/dev/ROADMAP.md`, "Now"):

- **Fixtures.** A small receptor + probe pair, committed, covering the basic grid-shape and
  rotation-level combinations.
- **Golden files.** Check generated `.dx` grids and docking energies against stored
  reference values, ideally cross-checked once against CHARMM's own binary grid dump
  (`DXGridUtil.read_charmm_grid_bin`) for at least one case.
- **Invariants.** Cheap properties that hold for any input: grid point counts match
  `points_per_dim`, probe coordinates stay centered after rotation, pose ranking is sorted.
- **Regression.** Every bug fix adds the test that would have caught it.

## Scientific validity and reproducibility

- Record provenance where output is written: crimm-dock version, grid parameters used
  (spacing, padding, Emax values, dielectric mode).
- When a bug could have produced wrong energies or poses, say so plainly and describe how a
  user can check systems already docked with the buggy version.

## Packaging and release

- One version source, in `pyproject.toml`.
- Reconsider committing compiled `.so` binaries (currently force-added despite `.gitignore`);
  prefer a documented build step per Python/platform.
- State the supported Python range and keep it in sync with what's actually been built
  (`docs/dev/AGENT_HANDOFF.md` environment facts note the current Python 3.12 gap).
- Licence: GPLv3 (matches crimm).

## Project management

- Track work as GitHub issues with acceptance criteria. Branches and pull requests link to
  them.
- Short-lived branches, deleted on merge. Squash-merge with a message that explains why.
- Commit and push only when the owner asks, each session.

## Working with AI coding tools

- Generated code gets the same review as any other, with extra attention to numerical
  details: atom order, index base, units, sign conventions, and whether a change to grid
  math was verified against the smallest possible case.
- Keep work orders for agents as GitHub issues, not loose Markdown files at the repo root.
- Do not commit agent scratch files or local tool settings; they go in `.gitignore` or, for
  files personal to one developer, `.git/info/exclude`.
- The root files for agents are `AGENTS.md` (the instructions) and `CLAUDE.md` (one line,
  `@AGENTS.md`).
