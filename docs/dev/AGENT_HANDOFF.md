# AGENT_HANDOFF

Shared memory for AI agents working on crimm-dock (package `crimm_dock`). Any model, any
tool. Written for agents first; humans read it second.

```yaml
schema: agent-handoff/1
repo: github.com/Truman-Xu/crimm-dock
default_branch: main
last_updated: 2026-11-09
log: open issue labelled agent-log   # gh issue list --label agent-log --state open
```

## 0. Protocol

Read this section fully. Skim the rest for what your task touches.

This file holds what changes rarely: protocol, orientation, the owner's standing
instructions, the environment and gotchas. What changes every session (STATE, CLAIMS and
LOG) is in the open GitHub issue labelled `agent-log` (section 5), so that recording a
session needs no commit.

### On arrival

1. Read sections 1 to 4. They are short and change rarely.
2. Read the `agent-log` issue: its description (CLAIMS and STATE) and its newest three
   comments (LOG). `N=$(gh issue list --label agent-log --state open --json number -q
   '.[0].number')`, then `gh issue view $N` and `gh issue view $N --comments`.
3. Run `git status --short` and `git log --oneline -5`. If they disagree with STATE, trust
   git and correct STATE.
4. Check CLAIMS before editing a file. If another agent holds it, do not edit it.

### On departure

1. Post one LOG entry as a comment on the `agent-log` issue (template in the issue
   description): `gh issue comment $N --body-file <file>`.
2. Update STATE so it is true now. Re-read the description immediately before, edit it in
   place, and write it back with `gh issue edit $N --body-file <file>`. Do not append.
3. Release your CLAIMS in the same edit.
4. Move anything you learned that will still be true next month into Orientation or Gotchas
   of this file. That is a tracked change; commit it with your work.

Without network access or `gh`, write the entry and the new STATE to local files and post
them in your next session that has both.

When the issue grows long (about 50 comments) or a milestone closes, open the next one
(label `agent-log`) with the current STATE, link it from the old one, then close the old one
and move the pin.

### Writing rules

- **Tag every claim with how you know it.** Use exactly one of:
  - `[ran]` you executed it and saw the result this session
  - `[read]` you read the code or file; did not execute
  - `[told]` the owner said so
  - `[inferred]` your conclusion; say from what
- **Date everything** as `YYYY-MM-DD`. Never write "today", "recently" or "currently".
- **Cite locations** as `path:line` or `path::symbol`. Prefer the symbol; line numbers rot.
- **State what you did not check.** A missing check written down is worth more than a
  confident guess.
- **One fact, one place.** Link to `NOTES.md` or `ROADMAP.md` instead of copying from them.
- **Do not edit or delete another agent's entry.** If it is wrong, say so in your own
  comment: `SUPERSEDED YYYY-MM-DD by <agent>: <why>`, with a link to the comment.
- **Identify yourself** as `<model>/<tool>/<short task name>`, for example
  `claude-sonnet/claude-code/project-setup`, in the heading of your log comment. Comments
  appear under the GitHub account the agent runs as, usually a person's; the heading is what
  tells sessions apart.
- **The log is public**, like this file. Nothing about a particular machine or account, and
  nothing about the CHARMM source read under Prof. Brooks's permission, goes here; the latter
  goes in the owner's `CLAUDE.local.md`.
- Keep entries terse. No preamble, no summaries of summaries.

### What goes where

| Kind of information | Place |
| --- | --- |
| How the code is built, package map, the C extension, the mixing-rule difference from CHARMM | `docs/dev/NOTES.md` |
| What work is planned, its order, its status | `docs/dev/ROADMAP.md` |
| Standards the work should meet | `docs/dev/BEST_PRACTICES.md` |
| Machine- and account-specific setup (paths, cluster, accounts), and anything from the licensed CHARMM source | the owner's `CLAUDE.local.md` (not in the repository) |
| Who is doing what now, current state, what was tried, what failed, decisions | the `agent-log` issue (section 5) |
| Questions an agent could not settle | an issue labelled `question` |
| Protocol, standing instructions, environment facts, traps | this file |

## 1. Orientation

- crimm-dock (package `crimm_dock`) is an FFT-grid docking extension for crimm: electrostatic
  and van der Waals potential grids for a receptor, correlated by FFT against rotated probe/
  ligand grids to rank poses. It reimplements the FASTDOCK and CDOCKER methods from the
  CHARMM family. `[told 2026-11-09]`
- Owner: Truman Xu (`Truman-Xu`), sole developer. `[told 2026-11-09]`
- **Reference implementation**: CHARMM's `fftdock.F90` and its CUDA/OpenCL/Metal kernels,
  at `~/charmm/source/fftdock` on the owner's machines. This is licensed CHARMM source,
  read under permission from Prof. Charles Brooks to reimplement the FFT-grid docking as
  crimm-dock. Never copy CHARMM source into this repository, issues, commit messages or PR
  descriptions; cite the method and file/line instead. `[told 2026-11-09]`
- **Reference papers**: FASTDOCK and CDOCKER (plus their SI), under `papers/`, git-ignored,
  never committed (the repository is public). `[told 2026-11-09]`
- **Documented difference from CHARMM**: this implementation uses the **geometric mean**
  for the van der Waals characteristic-length (`Rmin`/sigma) mixing rule —
  `Rmin_ij = sqrt(Rmin_i * Rmin_j)` — where CHARMM's native combining rule is the arithmetic
  sum of half-radii, `Rmin_ij = Rmin_i + Rmin_j`. `[told 2026-11-09]` Verified in the C
  source `[read 2026-11-09]`: `src/fft_docking/grid_gen.c::gen_all_grids` builds the
  receptor-side grid from `Rmin_i^3` and `Rmin_i^6` terms alone, and
  `src/fft_docking/lig_grid_gen.c::calc_vdw_energy_factors` builds the ligand-side factor the
  same way (`eps_sqrt * Rmin^3`, `eps_sqrt * Rmin^6`); the FFT correlation then multiplies
  the two fields, reconstructing `sqrt(eps_i*eps_j) * (Rmin_i*Rmin_j)^3` (attractive) and
  `^6` (repulsive) — i.e. the geometric mean of `Rmin`, raised to the LJ powers. This
  factorization is *only* exact under the geometric mean; CHARMM's arithmetic sum rule is
  not separable this way, which is presumably why the grid method needs the substitution.
  Do not revert this to match CHARMM without re-deriving the factorization.
- **Package map** `[read 2026-11-09]`:
  - `crimm_dock/GridShapes.py`: `_Grid` and its `CubeGrid`, `BoundingBoxGrid`,
    `TruncatedSphereGrid`, `ConvexHullGrid` subclasses — grid-point geometry only, no
    energies.
  - `crimm_dock/GridGenerator.py`: `GridCoordGenerator` (shared base),
    `ReceptorGridGenerator` (potential grids for a receptor over one of the 4 grid shapes),
    `ProbeGridGenerator` (rotated probe grids over a quaternion set),
    `PocketGridGenerator` (receptor grids restricted to a detected binding pocket, via
    `sklearn.cluster.DBSCAN` + `scipy.spatial.KDTree` cavity detection).
  - `crimm_dock/FFTDocker.py`: `FFTDocker` (rigid receptor, whole-grid docking) and
    `FFTPocketDocker` (pocket-restricted docking), both thin orchestrators over the C
    extension (`load_receptor`/`load_probe`, `dock`, `rank_poses`).
  - `crimm_dock/DXGridUtil.py`: write/read `.dx` grid files and CHARMM's own binary grid
    format (`read_charmm_grid_bin`, Fortran-unformatted, for cross-checking against the
    reference implementation's own grid dumps).
  - `src/fft_docking/`: the C extension (`py_bindings.c`, `grid_gen.c`/`.h` — receptor
    potential grids and pairwise distances, `lig_grid_gen.c` — probe rotation + trilinear
    grid deposition, `fft_correlate.c`/`.h` — FFTW3F-based correlation and grid summation,
    `rank_poses.c`/`.h` — top-N pose selection and pairwise RMSD). Built by `setup.py` as
    `crimm_dock.fft_docking`, linking `fftw3f`, `fftw3f_threads` and OpenMP.
  - `crimm_dock/Data/`: binary data the package loads at import/runtime —
    `quaternion-{1,2,3}.npy` (rotation search levels 1/2/3: 576, **4608**, 36864 rotations
    `[ran 2026-11-09]`; `GridGenerator.py::ProbeGridGenerator`'s docstring says "4068" for
    level 2 — that is a typo, the array is 4608, matching the FASTDOCK paper, tracked as
    #TBD), and (after the migration below) `Data/probes/` — probe molecule definitions
    moved here from crimm.
- **Probes moved from crimm** `[told 2026-11-09, done <date>]`: `crimm/Data/probes/` was
  orphaned dead code in crimm (flagged in
  [crimm#134](https://github.com/BrooksResearchGroup-UM/crimm/issues/134)), used only by
  crimm-dock. Moved to `crimm_dock/Data/probes/` wholesale (no deprecation shim in crimm —
  it was never a published/stable API). `GridGenerator.py` and `FFTDocker.py` import it as
  `crimm_dock.Data.probes.probes` now, not `crimm.Data.probes.probes`.
- **crimm dependency.** crimm-dock depends on crimm for structure entities
  (`crimm.StructEntities`), topology/parameter loading (`crimm.Modeller.ParameterLoader`),
  visualization (`crimm.Visualization.View`) and structure utilities
  (`crimm.Utils.StructureUtils.get_coords`). This repo only reads crimm; if a change is
  needed there, say so in your log entry and let the owner decide. `[read 2026-11-09]`

## 2. Standing instructions from the owner

| Date | Instruction | Tag |
| --- | --- | --- |
| 2026-11-09 | Set this project up for project management and agent logs the same way crimm and msld-prep are set up (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, handoff/notes/roadmap/best-practices docs, issue forms, `CODEOWNERS`, agent-log issue). | `[told]` |
| 2026-11-09 | Agent activity (state, claims, session log) is not kept in a tracked file. It goes in the open `agent-log` issue; open questions are issues labelled `question` (section 5). | `[told]` |
| 2026-11-09 | Untracked cruft (old C/CUDA/Rust experiments under `src/`, `.vscode/`, build artifacts) may be git-ignored as part of setup; anything ambiguous (e.g. `notebooks/ProbeDocking.ipynb`, the ad-hoc scripts in `tests/`) is flagged for the owner rather than silently resolved. | `[told]` |
| 2026-11-09 | Probes: move `crimm/Data/probes/` into crimm-dock as part of answering crimm#134, no deprecation shim left in crimm (it was dead/orphaned code, not a published API). `crimm/Utils/cuda_info.py` (also named in #134) is out of scope for this project; recommend its disposition in the #134 comment only, do not touch the code. | `[told]` |
| 2026-11-09 | OK to open pull requests (not merge) on both `Truman-Xu/crimm-dock` and `BrooksResearchGroup-UM/crimm` once work is ready, same pattern as msld-prep/crimm-ml. The owner reviews and merges. | `[told]` |

Working agreements carried over from crimm/msld-prep (not owner instructions for this
project; change them by logging why) `[inferred: same owner, same setup]`:

- Commit only when asked; never push unless asked. Permission for one session does not carry
  over to the next.
- Sign commits, never files.
- One concern per change. A fix does not ride along with a rename.
- A bug you find but do not fix gets a GitHub issue (no `xfail(strict=True)` test is possible
  yet — there is no test suite, see Gotchas G1).

## 3. Environment facts

Machine facts specific to a host go in `CLAUDE.local.md`, not here. What's below is true
regardless of machine.

| Fact | Tag |
| --- | --- |
| The C extension needs FFTW3F (`fftw3f`, `fftw3f_threads`) and an OpenMP runtime at build and link time (`setup.py`: `-fopenmp`/`gomp` for gcc, `-openmp`/`iomp5` for icc, `-fopenmp=libomp`/`omp` for clang). `conda install fftw` is the easiest source. | `[read setup.py]` |
| Two prebuilt `.so` files are committed to the repo (`crimm_dock/fft_docking.cpython-{39,310}-x86_64-linux-gnu.so`), despite `.gitignore` having `*.so` (they were force-added). They only cover Python 3.9 and 3.10. | `[ran 2026-11-09]` `git check-ignore -v` |
| **crimm-dev (Python 3.12, the shared dev env for crimm/msld-prep) has no FFTW3F installed and no matching compiled extension**, so `import crimm_dock` currently fails there with an `ImportError` that looks like a circular import (`cannot import name 'fft_docking' from partially initialized module 'crimm_dock'`) — the real cause is the missing/mismatched compiled module, surfaced through the self-referential `from crimm_dock import fft_docking` inside `FFTDocker.py`. Rebuilding for 3.12 (`conda install fftw` in `crimm-dev`, then `pip install -e .`) is untested as of this writing. | `[ran 2026-11-09]` |

## 4. Gotchas

| ID | Trap | Tag |
| --- | --- | --- |
| G1 | There is no real automated test suite. `tests/*.py` are ad-hoc exploration scripts (module-level code, no `def test_` functions, hardcoded dead paths like `/home/truman/crimm/src/grid_gen_simple.so`, calls to functions that no longer exist in the current `fft_docking` module, e.g. `fft_correlate.argsort`). Do not treat a clean `pytest` run as meaningful; there's nothing to collect. Building a real suite is ROADMAP's top item. | `[ran 2026-11-09]` |
| G2 | `crimm_dock` cannot currently be imported in `crimm-dev` (environment facts, above). Any claim of having "run" crimm-dock code in that env is false until the extension is rebuilt there. | `[ran 2026-11-09]` |
| G3 | `_Probe` subclasses in `Data/probes/probes.py` must set `_donors`/`_acceptors` (plural) to flag H-bond donor/acceptor atoms; `_Probe.__init__` reads exactly those names. `Acetaldehyde`, `Acetamide`, `AceticAcid` and `Acetonitrile` were found using the misspelled singular `_donor`/`_acceptor`, which silently falls back to the base class's empty defaults. Only `Acetaldehyde` had a non-empty intended value (`_acceptor = (3,)`, the carbonyl oxygen), so only its acceptor flag was actually lost. Currently inert: nothing in the C grid-generation code reads `H_donors`/`H_acceptors` yet (G4), so this has no live effect, but will matter the moment H-bond grids are implemented or any other code reads those lists. | `[read 2026-11-09]` |
| G4 | The C extension (`grid_gen.c`, `lig_grid_gen.c`) only computes electrostatic and van der Waals (attractive/repulsive) grids. CHARMM's reference GPU kernel (`generateProtGrid.cl`) additionally computes separate hydrogen-bond donor/acceptor directional grids (`NGrids-3`, `NGrids-2`). **Confirmed intentional** `[told 2026-11-09]`: not a gap to close, do not add H-bond grids as a "fix". | `[read 2026-11-09]`, `[told 2026-11-09]` |
| G5 | The paper's stated grid padding ("10 Å larger than the largest dimension of the protein", i.e. 5 Å half-width per side) does not match `FFTDocker.__init__`'s default `receptor_padding=8.0`. User-tunable, so not necessarily wrong, but don't assume the default reproduces the paper's benchmark numbers. | `[read 2026-11-09]` |
| G6 | The probe list in the FASTDOCK paper names 17 compounds while the paper's text says "18" (likely a manuscript erratum, not ours to fix). Of the 18 `_Probe` subclasses actually in the code: `AceticAcid` (resname "Acetic Acid") has **no carboxylic OH hydrogen and a net charge of −1** — it's chemically acetate, matching the paper's "acetate" probe name but not its own class/resname. `Cyclohexene` has a C=C double bond (`CG2D1` atoms), where the paper names "cyclohexane" (saturated). `DimethylEther` exists in code but isn't in the paper's list at all. None of these were touched; they're flagged as open questions. | `[ran 2026-11-09]` net-charge sum; `[read]` atom types and bonds |

## 5. State, claims, open questions and log

These change every session, so they are not kept in this file, which needs a commit for
every change:

- **State, claims and the log** are in the open issue labelled `agent-log`. Its description
  holds Claims and State, rewritten in place; each comment is one session's log entry. Find
  it with `gh issue list --label agent-log --state open`.
- **Open questions** are issues labelled `question`.
