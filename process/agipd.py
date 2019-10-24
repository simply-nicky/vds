"""
agipd.py - Apply AGIPD dark calibration
"""
import argparse
import numpy as np
import h5py
from .. import config

class DarkAGIPD(object):
    OFFSET_KEY = config.OFFSET_KEY
    BADMASK_KEY = config.BADMASK_KEY
    GAIN_LEVEL_KEY = config.GAIN_LEVEL_KEY
    MODULE_SHAPE = config.MODULE_SHAPE

    def __init__(self, filename, mask_inv=True):
        self.data_file = h5py.File(filename, 'r')
        self.mask_inv = mask_inv

    def offset(self, gain_mode, cell_id, module_id):
        return self.data_file[self.OFFSET_KEY][gain_mode, cell_id, module_id]

    def gain_level(self, gain_mode, cell_id, module_id):
        return self.data_file[self.GAIN_LEVEL_KEY][gain_mode, cell_id, module_id]

    def bad_mask(self, module_id):
        idxs = (slice(self.MODULE_SHAPE[0] * module_id, self.MODULE_SHAPE[0] * (module_id + 1)),)
        bad_mask = self.data_file[self.BADMASK_KEY][idxs]
        return 1 - bad_mask if self.mask_inv else bad_mask

class AGIPDVDS(object):
    TRAIN_KEY = config.AGIPD_TRAIN_KEY
    PULSE_KEY = config.AGIPD_PULSE_KEY
    CELL_KEY = config.AGIPD_CELL_KEY
    DATA_KEY = config.AGIPD_DATA_KEY
    GAIN_KEY = config.AGIPD_GAIN_KEY
    MODULE_KEY = config.AGIPD_MODULE_KEY

    def __init__(self, path):
        self.vds_file = h5py.File(path, 'r')
        self._init_data()

    def _init_data(self):
        self.cell_id = self.cell_ids[0]
        self.modules = self.vds_file[self.MODULE_KEY][:]

    @property
    def train_ids(self):
        return self.vds_file[self.TRAIN_KEY]

    @property
    def cell_ids(self):
        return self.vds_file[self.CELL_KEY]

    @property
    def pulse_ids(self):
        return self.vds_file[self.PULSE_KEY]

    @property
    def data(self):
        return self.vds_file[self.DATA_KEY]

    @property
    def gain(self):
        return self.vds_file[self.GAIN_KEY]

    def close(self):
        self.vds_file.close()


class AGIPDCalib(object):
    GAIN = np.array([config.HG_GAIN, config.MG_GAIN])
    FLAT_ROI = (0, 10)
    OUT_GROUP = config.AGIPD_CALIB_KEY

    def __init__(self, vds_file, dark):
        self.vds_file, self.dark = vds_file, dark
        self._init_adu()
        self._flat_correct()
        self._init_mask()
        self.data = ((self.adu * self.mask).T * self.GAIN).T

    def _init_adu(self):
        print("Subtracting offsets...")
        data = self.vds_file.data[:]
        print("Data shape: {}".format(data.shape))
        hg_adus = data - self.dark.offset(gain_mode=config.HIGH_GAIN,
                                                    cell_id=self.vds_file.cell_id,
                                                    module_id=self.vds_file.modules)
        mg_adus = data - self.dark.offset(gain_mode=config.MEDIUM_GAIN,
                                                    cell_id=self.vds_file.cell_id,
                                                    module_id=self.vds_file.modules)
        self.adu = np.stack((hg_adus, mg_adus))
        print("Done, ADU data shape: {}".format(self.adu.shape))

    def _flat_correct(self):
        print("Baseline correcting...")
        self.zero_levels = self.adu[0, :, self.FLAT_ROI[0]:self.FLAT_ROI[1]].mean(axis=(2, 3))
        self.adu[0] = (self.adu[0].T - self.zero_levels.T).T
        print("Done, zero levels: {}".format(self.zero_levels.mean(axis=0)))

    def _init_mask(self):
        print("Generating mask...")
        gain_levels = self.dark.gain_level(gain_mode=config.MEDIUM_GAIN,
                                           cell_id=self.vds_file.cell_id,
                                           module_id=self.vds_file.modules)
        gain = self.vds_file.gain[:]
        print("Gain shape: {}".format(gain.shape))
        hg_mask = (gain < gain_levels).astype(np.uint8)
        mg_mask = (gain > gain_levels).astype(np.uint8)
        bad_mask = np.stack([self.dark.bad_mask(module_id=module_id) for module_id in self.vds_file.modules])
        self.mask = np.stack((hg_mask, mg_mask)) * bad_mask
        print("Done, mask shape: {}".format(self.mask.shape))

    @property
    def calib_data(self):
        return self.data.sum(axis=0)

    def save_data(self, out_file):
        calib_group = out_file.create_group(self.OUT_GROUP)
        calib_group.create_dataset('adu', data=self.adu)
        calib_group.create_dataset('mask', data=self.mask)
        calib_group.create_dataset('data', data=self.data)

def apply_dark(path, dark_path):
    """
    Apply dark calibration

    path - path to VDS file with AGIPD data
    dark_path - path to dark AGIPD calibration file
    """
    vds_file = AGIPDVDS(path)
    dark = DarkAGIPD(dark_path)
    calib_data = AGIPDCalib(vds_file, dark)
    vds_file.close()
    print("Saving calibrated data to {}".format(path))
    out_file = h5py.File(path, 'r+')
    calib_data.save_data(out_file)

def main():
    parser = argparse.ArgumentParser(description="Apply AGIPD dark calibration")
    parser.add_argument('path', type=str, help="Path to VDS file")
    parser.add_argument('--config_file', type=str, default=config.CONFIG_PATH, help="Path to ini config file")

    args = parser.parse_args()
    conf_parser = config.ConfigParser(args.config_file)

    apply_dark(args.path, conf_parser.dark_path)
