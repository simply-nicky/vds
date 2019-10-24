import configparser
import numpy as np
import os

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SHELL_SCRIPT = os.path.join(PROJECT_ROOT, 'vds.sh')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.ini')

# AGIPD layout
MODULES_NUM = 16
MODULE_SHAPE = (512, 128)

# Raw data structure
AGIPD_KEY = 'MID_DET_AGIPD1M-1'
EPIX_KEY = 'INSTRUMENT/MID_EXP_EPIX-{:d}/DET/RECEIVER:daqOutput/data/image/pixels'
EPIX_TRAIN_KEY = 'INDEX/trainId'

# Raw file structure
GLOB_EPIX_KEY = '*-R{0:04d}-EPIX{1:02d}-S*.h5'
GLOB_AGIPD_KEY = '*-AGIPD{:02d}-S*.h5'

# Output file structure
AGIPD_TRAIN_KEY = 'data/AGIPD/index/trainId'
AGIPD_CELL_KEY = 'data/AGIPD/index/cellId'
AGIPD_PULSE_KEY = 'data/AGIPD/index/pulseId'
AGIPD_DATA_KEY = 'data/AGIPD/index/data'
AGIPD_GAIN_KEY = 'data/AGIPD/index/gain'
AGIPD_MODULE_KEY = 'data/AGIPD/moduleId'
EPIX_DATA_KEY = 'data/EPIX-{:d}/data'

# Dark calibration file structure
OFFSET_KEY = "AnalogOffset"
BADMASK_KEY = "Badpixel"
GAIN_LEVEL_KEY = "DigitalGainLevel"
AGIPD_CALIB_KEY = "data/AGIPD_calibrated"

# Dark calibration constants
HIGH_GAIN = 0
MEDIUM_GAIN = 1
LOW_GAIN = 2
HG_GAIN = 1 / 68.8
MG_GAIN = 1 / 1.376

class ConfigParser(object):
    """
    Class parser for ini files

    config_file - path to a config file
    """
    DATA_STRUCTURE = '{0:s}/r{1:04d}'

    def __init__(self, config_file):
        self.config_file = os.path.abspath(config_file)
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        self._init_data()
        self._init_batch()

    def _init_data(self):
        self.out_path = self.config.get('data', 'out_path')
        self.base_path = self.config.get('data', 'path')
        self.dark_path = self.config.get('data', 'dark_path')
        module_ids = [int(num) for num in self.config.get('data', 'modules').split()]
        self.modules_mask = np.zeros(MODULES_NUM, dtype=np.uint8)
        self.modules_mask[module_ids] = 1
        self.pulse_ids = np.array([int(num) for num in self.config.get('data', 'pulse_ids').split()])
        self.raw = self.config.getboolean('data', 'raw')
        self.tag = 'raw' if self.raw else 'proc'

    def _init_batch(self):
        self.run_start = self.config.getint('batch', 'run_start', fallback=0)
        self.run_end = self.config.getint('batch', 'run_end', fallback=0)

    def path(self, run_number):
        """
        Return path to experimental data
        """
        return os.path.join(self.base_path, self.DATA_STRUCTURE.format(self.tag, run_number))

class Module(object):
    """
    AGIPD module class with access keys to data

    key - AGIPD detector name
    module_id - AGIPD module number
    """
    def __init__(self, key, module_id):
        self.data = 'INSTRUMENT/{0}/DET/{1:d}CH0:xtdf/image/data'.format(key, module_id)
        self.pulses = 'INSTRUMENT/{0}/DET/{1:d}CH0:xtdf/image/pulseId'.format(key, module_id)
        self.cells = 'INSTRUMENT/{0}/DET/{1:d}CH0:xtdf/image/cellId'.format(key, module_id)
        self.trains = 'INSTRUMENT/{0}/DET/{1:d}CH0:xtdf/image/trainId'.format(key, module_id)
        self.trains_header = 'INSTRUMENT/{0}/DET/{1:d}CH0:xtdf/header/trainId'.format(key, module_id)
        self.pulse_count = 'INSTRUMENT/{0}/DET/{1:d}CH0:xtdf/header/pulseCount'.format(key, module_id)

class Imager(object):
    """
    Imager class with all the AGIPD modules

    key - AGIPD detector name
    """
    def __init__(self, key=AGIPD_KEY):
        self.key = key

    def module(self, module_id):
        return Module(self.key, module_id)