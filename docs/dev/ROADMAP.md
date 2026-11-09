# ROADMAP

An index of planned and in-progress work. Detail lives in the linked GitHub issues; this
file is the order and status, not the content.

## Now (blocking everything else)

| Item | Why it's first |
| --- | --- |
| `crimm_dock` cannot be imported in `crimm-dev` (Python 3.12): no FFTW3F in that env, no compiled extension for 3.12. See `docs/dev/AGENT_HANDOFF.md` environment facts. | Nothing else can be exercised or tested until the package actually imports in the shared dev environment. |
| No automated test suite (`tests/` holds ad-hoc scripts, not pytest tests). | Every other change below is unverifiable without this. Start with the smallest possible case: one receptor, one probe, one rotation, assert the grid/energy against a value computed by hand or against the CHARMM reference's own `.dx`/binary grid dump (`DXGridUtil.read_charmm_grid_bin`). |

## Bugs and discrepancies found in the 2026-11-09 audit

Filed as GitHub issues once labels existed; see the issue tracker for current status and
discussion. Listed here for the index:

- Rotation level docstring typo (4068 vs the actual/paper 4608).
- `AceticAcid` probe is chemically acetate (net charge −1, no carboxylic OH) despite its
  class/resname.
- `Cyclohexene` probe (C=C double bond) vs the paper's "cyclohexane" (saturated) — which one
  is intended?
- `DimethylEther` probe not in the paper's named list.
- Grid padding default (`receptor_padding=8.0`) vs the paper's implied 5 Å half-width.
- `_donor`/`_acceptor` (singular) misspelling in four probe classes, losing `Acetaldehyde`'s
  intended H-bond acceptor flag (currently inert, see Gotcha G4).
- `FFTDocker.dock()` has an open `TODO`: batch splitting for a large number of poses is not
  implemented.
- Compiled `.so` extension binaries are committed to git despite `.gitignore` having `*.so`
  (force-added) — packaging hygiene, worth reconsidering.

## Next

- A real pytest suite: fixture receptor + probe, golden grid/energy values, at least one
  regression test per bug above once fixed.
- Rebuild `crimm_dock.fft_docking` for the `crimm-dev` Python (3.12); confirm `fftw3f` via
  `conda install fftw` in that env.
- Resolve the probe-identity questions above (acetate naming, cyclohexene vs cyclohexane,
  dimethyl ether) with the owner, since they affect what the benchmark numbers in the papers
  actually correspond to.

## Later

- Batch splitting for large pose counts (`FFTDocker.dock()` TODO).
- Packaging: drop the committed `.so` binaries in favor of a documented build step; pin a
  crimm version once crimm's own API settles.

## Done

- Multi-entity receptor for FFT docking.
- Pocket docking via cavity detection (DBSCAN + KDTree).
- Docked probe pose offset fix (commit `8a2417f`).
- Project management setup (this round): `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, these
  `docs/dev/` files, issue forms, `CODEOWNERS`, the `agent-log` issue.
- Probes migrated from `crimm/Data/probes/` into `crimm_dock/Data/probes/`
  (crimm#134).
