# NOTES

How crimm-dock is built, its architecture and conventions. Targets, not a work log — the
`agent-log` issue has the current state.

## What it does

FFT-grid docking: build electrostatic and van der Waals potential grids for a receptor,
build the same for a probe or ligand at many rotations (quaternion search), correlate the
two by 3D FFT (equivalent to scanning every translation at once), and rank the resulting
poses by total energy. This is the method of FASTDOCK/CDOCKER (CHARMM family), reimplemented
here with crimm structures and a geometric-mean vdW mixing rule (see
`docs/dev/AGENT_HANDOFF.md`, Orientation, for why).

## Package map

| Path | Contents | Notes |
| --- | --- | --- |
| `crimm_dock/GridShapes.py` | `_Grid` base + `CubeGrid`, `BoundingBoxGrid`, `TruncatedSphereGrid`, `ConvexHullGrid` | Pure geometry: which grid points exist, no energies. `find_optimal_dims`/`is_divisible_by_2357` pick FFT-friendly grid dimensions (smallest size with only 2/3/5/7 as prime factors, like FFTW's preferred sizes). |
| `crimm_dock/GridGenerator.py` | `GridCoordGenerator` (shared base: loads an entity, exposes `coords`/`coord_center`/`max_dims`, builds any of the 4 grid shapes), `ReceptorGridGenerator`, `ProbeGridGenerator`, `PocketGridGenerator` | `get_nonbonded_dict`/`get_chain_nonbonded_dict` pick the right `ParameterLoader` (`protein`/`nucleic`/`cgenff`/`water_ions`) per chain type, then `_collect_params` pulls `charge`, `rmin_half` (×2 → `rmin`) and `epsilon` per atom from `atom.topo_definition`. |
| `crimm_dock/FFTDocker.py` | `FFTDocker` (rigid whole-grid docking), `FFTPocketDocker(FFTDocker)` (pocket-restricted) | Thin orchestration: `load_receptor`/`load_probe` → `dock()` (FFT correlate + sum grids) → `rank_poses()` (top-N selection + pose coordinate reconstruction via `_get_conf_coords`). |
| `crimm_dock/DXGridUtil.py` | `.dx` grid I/O, plus `read_charmm_grid_bin` (CHARMM's own Fortran-unformatted grid dump format) | The CHARMM-format reader is for cross-checking crimm-dock's grids directly against the reference implementation's own output — use it when validating a change to the grid formulas. |
| `src/fft_docking/` | The C extension, compiled as `crimm_dock.fft_docking` | See below. |
| `crimm_dock/Data/` | `quaternion-{1,2,3}.npy` (rotation search levels), `Data/probes/` (probe molecule library, moved from crimm) | Loaded via `os.path.join(os.path.dirname(__file__), 'Data')`, not a Python subpackage for the quaternion files (no `__init__.py` needed there); `Data/probes/` *is* a subpackage. |

## The C extension (`src/fft_docking/`)

| File | Role |
| --- | --- |
| `py_bindings.c` | Python/NumPy glue: argument parsing, dtype/shape checks, array ownership (`PyArray_ENABLEFLAGS(..., NPY_ARRAY_OWNDATA)`). No math here. |
| `grid_gen.c`/`.h` | `calc_grid_coord_pairwise_dist`, `gen_all_grids` — the receptor-side softcore electrostatic + vdW potential grids. |
| `lig_grid_gen.c` | Quaternion rotation (`quaternion_rotate`, `batch_quaternion_rotate`), `calc_vdw_energy_factors` (per-atom `eps_sqrt * Rmin^3` / `Rmin^6` factors — the ligand side of the geometric-mean mixing split), `gen_lig_grid`/`rotate_gen_lig_grids` (trilinear deposition of probe atom parameters onto a grid per rotation). |
| `fft_correlate.c`/`.h` | FFTW3F-based 3D correlation (`fft_correlate`: forward R2C FFT of the receptor grid once, forward R2C of each padded ligand grid, complex-conjugate multiply, inverse C2R) and `sum_grids` (collapse electrostatic + vdW-attr + vdW-rep into one score per grid point). |
| `rank_poses.c`/`.h` | Top-N pose selection via a bounded max-heap per orientation then combined (`rank_poses`, `combine_top_scores`), plus `calc_pairwise_rmsd` for pose clustering. |

Build: `setup.py` defines one `Extension` (`crimm_dock.fft_docking`) from the five `.c`
sources above, linking `fftw3f`, `fftw3f_threads`, `m` and an OpenMP runtime, with
`-Ofast -fopenmp` (or the compiler-appropriate flag). It is version- and
platform-specific — see `docs/dev/AGENT_HANDOFF.md` environment facts for the current gap
on Python 3.12.

## Conventions

- Single precision (`np.float32`) throughout the numeric path — "Single precision is enough
  for energy calculations" (`GridGenerator.py::_collect_params`). Don't silently widen to
  float64 passing into the C extension; it expects `NPY_FLOAT32` and will raise a
  `TypeError` otherwise (checked in `py_bindings.c`).
- `vdw_rs` collected from parameters is `rmin_half`; `_collect_params` doubles it to `rmin`
  before passing it on. If you add a new code path that reads vdW parameters, don't forget
  this factor of two.
- Quaternions are scalar-first (`w, x, y, z`), matching CHARMM's convention in
  `fftdock.F90::Rotate`/`QuaternionMultiply`.
- `GridCoordGenerator.coord_center` assumes the entity's coordinates are already centered/
  oriented (docstring: "Should return (0, 0, 0) after the transformation by
  `CoordManipulator.orient_coords()`"). crimm-dock does not itself orient a receptor to its
  principal axes of inertia the way the FASTDOCK paper describes; that step is crimm's
  `CoordManipulator`, applied by the caller before loading the entity here.
