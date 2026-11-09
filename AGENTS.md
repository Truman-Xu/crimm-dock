# Instructions for AI agents

crimm-dock (package `crimm_dock`) is a docking extension for crimm: FFT-grid docking of
small-molecule probes and ligands against a receptor, reimplementing the FASTDOCK/CDOCKER
method from the CHARMM family. It must stay buildable against crimm's released API and the
FFTW3F/OpenMP C extension in `src/fft_docking/`.

**Before doing anything, read [`docs/dev/AGENT_HANDOFF.md`](docs/dev/AGENT_HANDOFF.md)**
sections 0 to 4: protocol, the owner's standing instructions, environment facts and traps.
Current state, claims and the session log are in the open GitHub issue labelled `agent-log`
(`gh issue list --label agent-log --state open`): read its description and newest three
comments. Work is tracked as GitHub issues and indexed in
[`docs/dev/ROADMAP.md`](docs/dev/ROADMAP.md); standards are in
[`docs/dev/BEST_PRACTICES.md`](docs/dev/BEST_PRACTICES.md); developer rules, which bind you
too, are in [`CONTRIBUTING.md`](CONTRIBUTING.md). When you finish, post what you did as a
comment on that issue and update its State (handoff, section 0). That needs no pull request.

The rules that matter most, in case you read nothing else:

- Do not commit or push unless the owner asks. That permission does not carry over to a later
  session.
- Sign commits, never files: a `Co-Authored-By:` trailer naming your exact model; no author
  names, banners or session notes in any file.
- The reference implementation is CHARMM's `fftdock.F90` and its CUDA/OpenCL/Metal kernels
  under `~/charmm/source/fftdock` on the owner's machines (licensed CHARMM source, read with
  Prof. Brooks's permission; never copy it into this repository, issues or PRs). The reference
  papers (FASTDOCK, CDOCKER, their SI) are under `papers/`, git-ignored, never committed.
- **Documented difference from CHARMM**: this implementation uses the **geometric mean**
  (`Rmin_ij = sqrt(Rmin_i * Rmin_j)`) for the van der Waals characteristic-length mixing rule,
  where CHARMM uses the arithmetic sum (`Rmin_ij = Rmin_i + Rmin_j`). This is deliberate and
  required for the FFT grid decomposition (`Rmin_ij^12 = Rmin_i^6 * Rmin_j^6` only separates
  multiplicatively under the geometric mean). Do not silently revert it to match CHARMM.
- `crimm_dock` depends on `crimm` (topology/parameter loading, structure entities, probes).
  This repo only reads crimm; if a change is needed there, say so in your log entry and let
  the owner decide. crimm's own handoff lists this project under "What goes where".
- The hydrogen-bond donor/acceptor grid gap versus CHARMM's reference kernel is confirmed
  intentional (`docs/dev/AGENT_HANDOFF.md` Gotcha G4) — do not add it as a "fix".
- A bug you find but do not fix gets an `xfail(strict=True)` test with the reason and a GitHub
  issue (there is no real test suite yet — see `docs/dev/NOTES.md` — so for now this means a
  GitHub issue with a minimal reproduction, labelled `bug` or `correctness`).
- One concern per change. A fix does not ride along with a rename.
- A `TODO` in code carries an issue number.
- Personal notes of the owner live in `CLAUDE.local.md`, which is not in the repository. Facts
  about the owner's machine and account go there, not in `docs/dev/`.
