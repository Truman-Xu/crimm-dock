import os
import subprocess
from setuptools import setup, Extension
import numpy

CONDA_INCLUDE_DIR = './'
CONDA_LIB_DIR = './'
if 'CONDA_PREFIX' in os.environ:
    conda_path = os.environ['CONDA_PREFIX']
    CONDA_INCLUDE_DIR = os.path.join(conda_path, 'include')
    CONDA_LIB_DIR = os.path.join(conda_path, 'lib')

CC = os.environ.get('CC')
if CC is None:
    out = subprocess.check_output('cc --version', shell=True).decode('utf-8').lower()
    if "gcc" in out:
        CC = "gcc"
    elif "icc" in out:
        CC = "icc"
    elif "clang" in out:
        CC = "clang"
    else:
        raise ValueError(
            "No compiler detected, please set the CC environment variable."
        )

if CC == "gcc":
    OMP_FLAG = "-fopenmp"
    OMP_LIB = "gomp"
elif CC == "icc":
    OMP_FLAG = "-openmp"
    OMP_LIB = "iomp5"
elif CC == "clang":
    OMP_FLAG = "-fopenmp=libomp"
    OMP_LIB = "omp"
else:
    raise ValueError(
        f"Unknown compiler {CC} detected, please use gcc, icc, or clang."
    )


# Define the extension module
fft_correlate_module = Extension(
    'crimm_dock.fft_docking', 
    sources=[
        'src/fft_docking/py_bindings.c',
        'src/fft_docking/fft_correlate.c',
        'src/fft_docking/rank_poses.c',
        'src/fft_docking/grid_gen.c',
        'src/fft_docking/lig_grid_gen.c'
    ],
    include_dirs=[
        numpy.get_include(),
        CONDA_INCLUDE_DIR,
        './'
    ],
    libraries=['fftw3f', 'fftw3f_threads', 'm', OMP_LIB],
    library_dirs=[
        CONDA_LIB_DIR,
    ],
    define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
    extra_compile_args=[
        '-fPIC',
        '-Ofast', 
        '-g',
        OMP_FLAG
    ]
)

setup(
    ext_modules=[fft_correlate_module]
)
