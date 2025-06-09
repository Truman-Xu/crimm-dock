import multiprocessing
import numpy as np
# This is a C extension module compiled from src/fft_docking/py_bindings.c
from crimm_dock import fft_docking
from .GridGenerator import ReceptorGridGenerator, ProbeGridGenerator, PocketGridGenerator
from .GridShapes import CubeGrid

class FFTDocker:
    def __init__(
            self, grid_spacing=1.0, receptor_padding=8.0,
            effective_grid_shape='convex_hull', optimize_grids_for_fft=True,
            rad_dielec_const=2.0,
            elec_rep_max=40, elec_attr_max=-20,
            vdw_rep_max=2.0, vdw_attr_max=-2.0, use_constant_dielectric=False,
            rotation_level=2, custom_rotations=None,
            n_top_poses=2000, reduce_sample_factor=10,
            n_threads=None
        ):
        if n_threads is None:
            n_threads = multiprocessing.cpu_count()
        self.n_threads = n_threads
        self.grid_spacing = grid_spacing
        self.receptor_padding = receptor_padding
        self.optimize_grids_for_fft = optimize_grids_for_fft
        self.effective_grid_shape = effective_grid_shape
        self.rad_dielec_const = rad_dielec_const
        self.elec_rep_max = elec_rep_max
        self.elec_attr_max = elec_attr_max
        self.vdw_rep_max = vdw_rep_max
        self.vdw_attr_max = vdw_attr_max
        self.use_constant_dielectric = use_constant_dielectric
        self.rotation_level = rotation_level
        self.n_top_poses = n_top_poses
        self.reduce_sample_factor = reduce_sample_factor

        self.recep_gen = ReceptorGridGenerator(
            grid_spacing=self.grid_spacing,
            paddings=self.receptor_padding,
            optimize_for_fft=self.optimize_grids_for_fft,
            rad_dielec_const=self.rad_dielec_const,
            elec_rep_max=self.elec_rep_max,
            elec_attr_max=self.elec_attr_max,
            vdw_rep_max=self.vdw_rep_max,
            vdw_attr_max=self.vdw_attr_max,
            use_constant_dielectric=False
        )
        self.probe_gen = ProbeGridGenerator(
            grid_spacing=self.grid_spacing,
            rotation_search_level=self.rotation_level,
            custom_rotations=custom_rotations
        )
        ## These are the outputs from docking
        self.conf_coords = None
        self.position_id = None
        self.orientation_id = None
        self.top_scores = None
        self.total_energy = None
        self.result = None

    def load_receptor(self, receptor):
        self.conf_coords = None
        self.position_id = None
        self.orientation_id = None
        self.top_scores = None
        self.total_energy = None
        self.result = None
        self.recep_gen.load_entity(receptor, grid_shape=self.effective_grid_shape)

    def load_probe(self, probe):
        self.probe_gen.load_probe(probe)

    @property
    def receptor_grids(self):
        return self.recep_gen.get_potential_grids()

    @property
    def probe_grids(self):
        return self.probe_gen.get_param_grids()

    # TODO: Implement batch splitting for large number of poses
    def dock(self):
        if self.receptor_grids is None or self.probe_grids is None:
            raise ValueError('Receptor and Probe must be loaded before docking')

        self.result = fft_docking.fft_correlate(
            self.receptor_grids, self.probe_grids, self.n_threads
        )
        self.total_energy = fft_docking.sum_grids(self.result)

    def dock_single_pose(self, pose_coords):
        if self.receptor_grids is None or self.probe_grids is None:
            raise ValueError('Receptor and Probe must be loaded before docking')
        pose_coords = np.expand_dims(pose_coords.astype(np.float32),0)
        pose_grids = self.probe_gen.generate_grids_single_pose(pose_coords)
        result = fft_docking.fft_correlate(
            self.receptor_grids, pose_grids, self.n_threads
        )
        return np.squeeze(result)

    def rank_poses(self):
        self.top_scores, self.position_id, self.orientation_id = fft_docking.rank_poses(
            self.total_energy,
            top_n_poses=self.n_top_poses,
            sample_factor=self.reduce_sample_factor,
            n_threads=self.n_threads
        )
        self.conf_coords = self._get_conf_coords(self.position_id, self.orientation_id)
        return self.top_scores, self.conf_coords

    def _get_conf_coords(self, position_id, orientation_id):
        selected_ori_coord = self.probe_gen.rotated_coords[orientation_id]
        coord_grid = self.recep_gen.coord_grid
        if isinstance(coord_grid, CubeGrid):
            dists_to_recep_grid = coord_grid.coords[position_id]
        else:
            dists_to_recep_grid = self.recep_gen.bounding_box_grid.coords[position_id]
        
        # Add distance to origin and the half widths of the probe to the coordinates to shift it back
        offsets = dists_to_recep_grid + selected_ori_coord.ptp(1)/2
        conf_coords = selected_ori_coord+offsets[:,np.newaxis,:]
        
        # conf_coords += self.grid_spacing*np.array([1.0,1.0,1.0], dtype=np.float32)
        return conf_coords
    
    def save_receptor_grids(self, prefix: str):
        vdwa = self.recep_gen.get_attr_vdw_grid(False)
        vdwr = self.recep_gen.get_rep_vdw_grid(False)
        elec = self.recep_gen.get_elec_grid(False)
        if not isinstance(prefix, str):
            raise TypeError('Prefix has to be string!')
        self.recep_gen.save_dx(prefix+'_attr_vdw.dx', vdwa)
        self.recep_gen.save_dx(prefix+'_rep_vdw.dx', vdwr)
        self.recep_gen.save_dx(prefix+'_elec.dx', elec)
    
class FFTPocketDocker(FFTDocker):
    def __init__(
        self, grid_spacing=0.5,
        optimize_grids_for_fft=True,
        rad_dielec_const=2.0,
        elec_rep_max=40, elec_attr_max=-20,
        vdw_rep_max=2.0, vdw_attr_max=-2.0, use_constant_dielectric=False,
        rotation_level=2, custom_rotations=None,
        n_top_poses=2000, reduce_sample_factor=10,
        n_threads=None
    ):
        super().__init__(
            grid_spacing, 0.0,
            'bounding_box', optimize_grids_for_fft,
            rad_dielec_const,
            elec_rep_max, elec_attr_max,
            vdw_rep_max, vdw_attr_max, use_constant_dielectric,
            rotation_level, custom_rotations,
            n_top_poses, reduce_sample_factor,
            n_threads
        )
        self.recep_gen = PocketGridGenerator(
            grid_spacing=self.grid_spacing,
            optimize_for_fft=self.optimize_grids_for_fft,
            rad_dielec_const=self.rad_dielec_const,
            elec_rep_max=self.elec_rep_max,
            elec_attr_max=self.elec_attr_max,
            vdw_rep_max=self.vdw_rep_max,
            vdw_attr_max=self.vdw_attr_max,
            use_constant_dielectric=False
        )


    def load_receptor(self, receptor, box_dims, pocket_center=None, ref_ligand=None):
        if receptor.level != 'C':
            raise ValueError('Only Chain level entities are supported for docking')
        if not receptor.is_continuous():
            raise ValueError('Missing residues detected in the receptor entity. Please fill the gaps first.')
        ## These are the outputs from docking
        self.conf_coords = None
        self.position_id = None
        self.orientation_id = None
        self.top_scores = None
        self.total_energy = None
        self.result = None
        self.recep_gen.load_receptor(receptor, box_dims, pocket_center, ref_ligand)

    def save_receptor_grids(self, prefix: str):
        vdwa = self.recep_gen.get_attr_vdw_grid()
        vdwr = self.recep_gen.get_rep_vdw_grid()
        elec = self.recep_gen.get_elec_grid()
        if not isinstance(prefix, str):
            raise TypeError('Prefix has to be string!')
        self.recep_gen.save_dx(prefix+'_attr_vdw.dx', vdwa)
        self.recep_gen.save_dx(prefix+'_rep_vdw.dx', vdwr)
        self.recep_gen.save_dx(prefix+'_elec.dx', elec)