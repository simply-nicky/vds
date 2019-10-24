"""
vds_process.py - Create a VDS HDF5 file for the given run
"""
import os
import argparse
import h5py
import numpy as np
from datetime import datetime
from glob import glob
from functools import reduce
from .. import config
from .agipd import apply_dark

def process_epix(epix_descriptor, epix_id):
    """
    Process EPIX detector files

    epix_descriptor - list of EPIX files
    epix_id - EPIX detector number
    """
    epix_shape = h5py.File(epix_descriptor[0], 'r')[config.EPIX_KEY.format(epix_id)].shape[1:]
    epix_trains = [h5py.File(descriptor, 'r')[config.EPIX_TRAIN_KEY][:]
                   for descriptor in epix_descriptor]
    return np.concatenate(epix_trains), epix_shape

def process_agipd(path, modules_mask, imager):
    """
    Process AGIPD detector files

    path - path to experimental data
    modules_mask - which AGIPD modules to process
    imager - Imager class object
    """
    agipd_trains, agipd_descriptor = [], []
    trains_size = 0

    for module_id, flag in enumerate(modules_mask):
        if flag:
            descriptor = sorted(glob(os.path.join(path, config.GLOB_AGIPD_KEY.format(module_id))))
            if descriptor:
                module_trains = process_module(descriptor, imager, module_id)
                agipd_descriptor.append(descriptor)
                agipd_trains.append(module_trains)
                trains_size += module_trains.size
            else:
                modules_mask[module_id] = 0
    trains = reduce(np.intersect1d, agipd_trains)

    agipd_data = {'trains': trains,
                  'modules': np.arange(config.MODULES_NUM)[modules_mask == 1],
                  'descriptor': agipd_descriptor,
                  'trains_size': trains_size}
    return agipd_data

def process_module(module_descriptor, imager, module_id):
    """
    Process AGIPD module files

    module_descriptor - list of AGIPD module files
    imager - Imager clas object
    module_id - AGIPD module number
    """
    print("Processing AGIPD module {:d}".format(module_id))
    print("Number of files to process: {:d}".format(len(module_descriptor)))

    module_trains = []
    for descriptor in module_descriptor:
        with h5py.File(descriptor, 'r') as data_file:
            trains_1 = data_file[config.EPIX_TRAIN_KEY][:]
            trains_2 = data_file[imager.module(module_id).trains_header][:]
            trains = np.intersect1d(trains_1, trains_2)
            module_trains.append(trains)

    module_trains = np.concatenate(module_trains)
    print("Module {0:d} processed, trains shape: {1}".format(module_id,
                                                             module_trains.shape))
    return module_trains

def save_agipd(out_file, agipd_data, pulse_ids, imager):
    """
    Save AGIPD data to a VDS HDF5 file

    out_file - HDF5 file
    agipd_data - AGIPD data dictionary
    pulse_ids - pulse IDs to save
    imager - Imager class object
    """
    frames = agipd_data['trains'].size * pulse_ids.size
    data_layout = h5py.VirtualLayout(shape=(frames, agipd_data['modules'].size) + config.MODULE_SHAPE, dtype=np.uint16)
    gain_layout = h5py.VirtualLayout(shape=(frames, agipd_data['modules'].size) + config.MODULE_SHAPE, dtype=np.uint16)
    train_dset = out_file.create_dataset(config.AGIPD_TRAIN_KEY, shape=(frames,), dtype=np.uint16)
    cell_dset = out_file.create_dataset(config.AGIPD_CELL_KEY, shape=(frames,), dtype=np.uint16)
    pulse_dset = out_file.create_dataset(config.AGIPD_PULSE_KEY, shape=(frames,), dtype=np.uint64)
    for idx, (module_id, descriptor) in enumerate(zip(agipd_data['modules'],
                                                      agipd_data['descriptor'])):
        counter = 0
        print('\nProcessing AGIPD{:02d}'.format(module_id))
        for file_name in descriptor:
            print('Opening file: {}'.format(os.path.basename(file_name)))
            module = imager.module(module_id)
            with h5py.File(file_name, 'r') as data_file:
                file_trains = data_file[module.trains][:].ravel()
                file_pulses = data_file[module.pulses][:].ravel()
                file_cells = data_file[module.cells][:].ravel()
                file_data = data_file[module.data]
                if file_trains.size > 0:
                    train_mask = np.isin(file_trains, agipd_data['trains'])
                    pulse_mask = np.isin(file_pulses, pulse_ids)
                    file_idxs = np.nonzero(train_mask & pulse_mask)[0]

                    train_dset[counter:counter + file_idxs.size] = file_trains[file_idxs]
                    pulse_dset[counter:counter + file_idxs.size] = file_pulses[file_idxs]
                    cell_dset[counter:counter + file_idxs.size] = file_cells[file_idxs]

                    chunk_size = file_data.chunks[0]
                    num_chunks = np.ceil(file_idxs.size / chunk_size).astype(np.int)
                    for chunk in range(num_chunks):
                        start, end = chunk * chunk_size, min(file_data.shape[0],
                                                             (chunk + 1) * chunk_size)
                        data = h5py.VirtualSource(file_data)[file_idxs[start:end], 0]
                        gain = h5py.VirtualSource(file_data)[file_idxs[start:end], 1]
                        data_layout[counter:counter + file_idxs[start:end].size, idx] = data
                        gain_layout[counter:counter + file_idxs[start:end].size, idx] = gain
                        counter += file_idxs[start:end].size
            print('File {0} saved, data size: {1:d}\n'.format(os.path.basename(file_name), counter))
    out_file.create_virtual_dataset(config.AGIPD_DATA_KEY, data_layout)
    out_file.create_virtual_dataset(config.AGIPD_GAIN_KEY, gain_layout)

def save_epix(out_file, descriptor, trains, shape, epix_id):
    """
    Save EPIX data to a VDS HDF5 file

    out_file - HDF5 file
    descriptor - list of data files to save
    trains - train IDs to save
    shape - EPIX data shape
    epix_id - EPIX detector number
    """
    layout = h5py.VirtualLayout(shape=(trains.size,) + shape, dtype=np.uint16)
    counter = 0
    for file_name in descriptor:
        print('Opening file: {}'.format(os.path.basename(file_name)))
        with h5py.File(file_name, 'r') as data_file:
            file_trains = data_file[config.EPIX_TRAIN_KEY][:]
            file_data = data_file[config.EPIX_KEY.format(epix_id)]
            file_idxs = np.concatenate([np.where(train_id == file_trains)[0]
                                        for train_id in trains])
            chunk_size = file_data.chunks[0]
            num_chunks = int(np.ceil(file_idxs.size / chunk_size))
            for chunk in range(num_chunks):
                start, end = chunk * chunk_size, min(file_data.shape[0],
                                                     (chunk + 1) * chunk_size)
                data = h5py.VirtualSource(file_data)[file_idxs[start:end], :, :]
                layout[counter:counter + file_idxs[start:end].size] = data
                counter += file_idxs[start:end].size
        print('File {0} saved, data size: {1:d}\n'.format(os.path.basename(file_name), counter))
    out_file.create_virtual_dataset(config.EPIX_DATA_KEY.format(epix_id), layout)

def create_vds(conf_parser, run_number):
    """
    Create VDS file of EPIX-1, EPIX-2 and AGIPD detectors data

    config - ConfigParser class object of ini config file
    run_number - run number
    """
    path = conf_parser.path(run_number)
    print("Run {0} at path: '{1}'".format(run_number, path))

    # EPIX-1
    e1_descriptor = sorted(glob(os.path.join(path, config.GLOB_EPIX_KEY.format(run_number, 1))))
    if e1_descriptor:
        e1_trains, e1_shape = process_epix(e1_descriptor, epix_id=1)

    # EPIX-2
    e2_descriptor = sorted(glob(os.path.join(path, config.GLOB_EPIX_KEY.format(run_number, 2))))
    if e2_descriptor:
        e2_trains, e2_shape = process_epix(e2_descriptor, epix_id=2)

    # AGIPD
    imager = config.Imager()
    agipd_descriptor = sorted(glob(os.path.join(path, config.GLOB_AGIPD_KEY.format(0))))
    if agipd_descriptor:
        agipd_data = process_agipd(path, conf_parser.modules_mask, imager)

    # Bad run number
    if not e1_descriptor and not e2_descriptor and not agipd_descriptor:
        raise ValueError("No files, bad run number {:d}".format(run_number))
    else:
        num_files = np.sum([len(desc) for desc in agipd_data['descriptor']])
        print("Number of files:")
        print("AGIPD: {:d}".format(num_files))
        print("EPIX1: {:d}".format(len(e1_descriptor)))
        print("EPIX1: {:d}".format(len(e2_descriptor)))

    # Intersect AGIPD and EPIX
    if agipd_descriptor and e1_descriptor:
        agipd_data['trains'], _, e1_indxs = np.intersect1d(agipd_data['trains'],
                                                           e1_trains,
                                                           assume_unique=False,
                                                           return_indices=True)
        e1_trains = e1_trains[e1_indxs]

    if agipd_descriptor and e2_descriptor:
        agipd_data['trains'], _, e2_indxs = np.intersect1d(agipd_data['trains'],
                                                           e2_trains,
                                                           assume_unique=False,
                                                           return_indices=True)
        e2_trains = e2_trains[e2_indxs]

    # Print information
    print("├── {0} trains (originally {1}) in [{2}, {3}]".format(agipd_data['trains'].size,
                                                                 agipd_data['trains_size'] // agipd_data['modules'].size,
                                                                 agipd_data['trains'][0],
                                                                 agipd_data['trains'][-1]))
    print("├── {0:d} pulses per train, Pulse ID: {1}".format(conf_parser.pulse_ids.size, conf_parser.pulse_ids))
    print("└── {0:d} frames in total\n".format(agipd_data['trains'].size * conf_parser.pulse_ids.size))

    if agipd_descriptor:
        module_size = config.MODULES_NUM * config.MODULE_SHAPE[-2] * config.MODULE_SHAPE[-1]
        print("{} detector".format(config.AGIPD_KEY))
        print("├── {0:d} modules: {1}".format(config.MODULES_NUM, agipd_data['modules']))
        print("└── {0:d}x{1:d} pixels per module, {2:d} in total\n".format(config.MODULE_SHAPE[-2],
                                                                           config.MODULE_SHAPE[-1],
                                                                           module_size))

    if e1_descriptor:
        e1_size = e1_shape[-2] * e1_shape[-1]
        print("{} detector".format('EPIX-01'))
        print("└── {0:d}x{1:d} pixels per module, {2:d} in total\n".format(e1_shape[-2],
                                                                           e1_shape[-1],
                                                                           e1_size))

    if e2_descriptor:
        e2_size = e2_shape[-2] * e2_shape[-1]
        print("{} detector".format('EPIX-02'))
        print("└── {0:d}x{1:d} pixels per module, {2:d} in total\n".format(e2_shape[-2],
                                                                           e2_shape[-1],
                                                                           e2_size))

    # Save data
    out_path = os.path.join(conf_parser.out_path, 'hdf5/r{:04d}.h5').format(run_number)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out_file = h5py.File(out_path, 'w', libver='latest')
    out_file.attrs['data'] = str(datetime.now())

    out_file['index/run'] = run_number
    out_file['index/stream'] = conf_parser.tag
    out_file['index/trainId'] = agipd_data['trains']
    out_file[config.AGIPD_MODULE_KEY] = agipd_data['modules']

    # AGIPD
    if agipd_descriptor:
        save_agipd(out_file=out_file,
                   agipd_data=agipd_data,
                   pulse_ids=conf_parser.pulse_ids,
                   imager=imager)

    # EPIX-1
    if e1_descriptor:
        save_epix(out_file=out_file,
                  descriptor=e1_descriptor,
                  trains=e1_trains,
                  shape=e1_shape,
                  epix_id=1)

    # EPIX-2
    if e1_descriptor:
        save_epix(out_file=out_file,
                  descriptor=e2_descriptor,
                  trains=e2_trains,
                  shape=e2_shape,
                  epix_id=2)

    out_file.close()
    print("Run {:d} has been saved to file {:s}".format(run_number, out_path))
    return out_path

def main():
    parser = argparse.ArgumentParser(description="Create a VDS file for given run number of EXFEL MID beam time")
    parser.add_argument('run_number', type=int, help="run number to process")
    parser.add_argument('--config_file', type=str, default=config.CONFIG_PATH, help="Path to ini config file")
    parser.add_argument('--calib', action="store_true", help="Apply dark calibration data to AGIPD detector")

    args = parser.parse_args()
    conf_parser = config.ConfigParser(args.config_file)

    out_path = create_vds(conf_parser=conf_parser, run_number=args.run_number)

    if args.calib:
        apply_dark(out_path, conf_parser.dark_path)
    