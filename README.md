# HDF5 VDS file generator for MID beamtime

This package creates an HDF5 VDS file based on AGIPD, EPIX-1 and EPIX-2 detectors data from XFEL MID beamtime. The package is written in Python.

## Features

The package creates a VDS file with given Pulse IDs frames for every Train ID of AGIPD data and all the fromes of EPIX detectors data. It applies dark calibration to AGIPD data and saves it in the same file. The package also can save only given AGIPD modules instead all of them.

## Required dependencies:

- NumPy
- h5py

## Data structure:

- data - all the detector frames
    - AGIPD - raw AGIPD data
        - index - AGIPD data
            - cellId - Cell IDs, data shape: (Train ID)
            - data - raw ADU data, data shape: (Train ID, Module ID, 512, 128)
            - gain - raw gain data, data shape: (Train ID, Module ID, 512, 128)
            - pulseId - Pulse IDs, data shape: (Train ID)
            - trainId - Train IDs, data shape: (Train ID)
        - moduleId - AGIPD module IDs saved, data shape: (Module ID)
    - EPIX-1 / EPIX-2
        - data - raw EPIX data, data shape: (Train ID, 708, 768)
    - AGIPD_corrected - dark calibrated AGIPD data
        - adu - dark offset subtracted ADU data, data shape: (Gain mode, Train ID, Module ID, 512, 128)
        - data - calibrated ADU data, data shape: (Gain mode, Train ID, Module ID, 512, 128)
        - mask - gain mode mask, data shape: (Gain mode, Train ID, Module ID, 512, 128)
- index - miscellanious info
    - run - Run number
    - stream - raw or proc stream
    - trainId - Train IDs

## How to use

You can use a package as a terminal tool to generate a file locally:

```
$ python -m vds.process --help

usage: __main__.py [-h] [--config_file CONFIG_FILE] [--calib] run_number

Create a VDS file for given run number of EXFEL MID beam time

positional arguments:
  run_number            run number to process

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        Path to ini config file
  --calib               Apply dark calibration data to AGIPD detector

$ python -m vds.process 110 --calib

Run 110 at path: '/gpfs/exfel/exp/MID/201901/p002543/raw/r0110'
Processing AGIPD module 13
Number of files to process: 10
Module 13 processed, trains shape: (2402,)
Processing AGIPD module 14
Number of files to process: 10
Module 14 processed, trains shape: (2408,)
Number of files:
AGIPD: 20
EPIX1: 3
EPIX1: 3
├── 2398 trains (originally 2405) in [567143593, 567146004]
├── 1 pulses per train, Pulse ID: [4]
└── 2398 frames in total

MID_DET_AGIPD1M-1 detector
├── 16 modules: [13 14]
└── 512x128 pixels per module, 1048576 in total

EPIX-01 detector
└── 708x768 pixels per module, 543744 in total

EPIX-02 detector
└── 708x768 pixels per module, 543744 in total


Processing AGIPD13
Opening file: RAW-R0110-AGIPD13-S00000.h5
File RAW-R0110-AGIPD13-S00000.h5 saved, data size: 255

Opening file: RAW-R0110-AGIPD13-S00001.h5
File RAW-R0110-AGIPD13-S00001.h5 saved, data size: 510

Opening file: RAW-R0110-AGIPD13-S00002.h5
File RAW-R0110-AGIPD13-S00002.h5 saved, data size: 766

Opening file: RAW-R0110-AGIPD13-S00003.h5
File RAW-R0110-AGIPD13-S00003.h5 saved, data size: 1021

Opening file: RAW-R0110-AGIPD13-S00004.h5
File RAW-R0110-AGIPD13-S00004.h5 saved, data size: 1276

Opening file: RAW-R0110-AGIPD13-S00005.h5
File RAW-R0110-AGIPD13-S00005.h5 saved, data size: 1530

Opening file: RAW-R0110-AGIPD13-S00006.h5
File RAW-R0110-AGIPD13-S00006.h5 saved, data size: 1782

Opening file: RAW-R0110-AGIPD13-S00007.h5
File RAW-R0110-AGIPD13-S00007.h5 saved, data size: 2037

Opening file: RAW-R0110-AGIPD13-S00008.h5
File RAW-R0110-AGIPD13-S00008.h5 saved, data size: 2292

Opening file: RAW-R0110-AGIPD13-S00009.h5
File RAW-R0110-AGIPD13-S00009.h5 saved, data size: 2398


Processing AGIPD14
Opening file: RAW-R0110-AGIPD14-S00000.h5
File RAW-R0110-AGIPD14-S00000.h5 saved, data size: 255

Opening file: RAW-R0110-AGIPD14-S00001.h5
File RAW-R0110-AGIPD14-S00001.h5 saved, data size: 510

Opening file: RAW-R0110-AGIPD14-S00002.h5
File RAW-R0110-AGIPD14-S00002.h5 saved, data size: 766

Opening file: RAW-R0110-AGIPD14-S00003.h5
File RAW-R0110-AGIPD14-S00003.h5 saved, data size: 1021

Opening file: RAW-R0110-AGIPD14-S00004.h5
File RAW-R0110-AGIPD14-S00004.h5 saved, data size: 1276

Opening file: RAW-R0110-AGIPD14-S00005.h5
File RAW-R0110-AGIPD14-S00005.h5 saved, data size: 1530

Opening file: RAW-R0110-AGIPD14-S00006.h5
File RAW-R0110-AGIPD14-S00006.h5 saved, data size: 1782

Opening file: RAW-R0110-AGIPD14-S00007.h5
File RAW-R0110-AGIPD14-S00007.h5 saved, data size: 2037

Opening file: RAW-R0110-AGIPD14-S00008.h5
File RAW-R0110-AGIPD14-S00008.h5 saved, data size: 2292

Opening file: RAW-R0110-AGIPD14-S00009.h5
File RAW-R0110-AGIPD14-S00009.h5 saved, data size: 2398

Opening file: RAW-R0110-EPIX01-S00000.h5
File RAW-R0110-EPIX01-S00000.h5 saved, data size: 997

Opening file: RAW-R0110-EPIX01-S00001.h5
File RAW-R0110-EPIX01-S00001.h5 saved, data size: 1989

Opening file: RAW-R0110-EPIX01-S00002.h5
File RAW-R0110-EPIX01-S00002.h5 saved, data size: 2398

Opening file: RAW-R0110-EPIX02-S00000.h5
File RAW-R0110-EPIX02-S00000.h5 saved, data size: 997

Opening file: RAW-R0110-EPIX02-S00001.h5
File RAW-R0110-EPIX02-S00001.h5 saved, data size: 1989

Opening file: RAW-R0110-EPIX02-S00002.h5
File RAW-R0110-EPIX02-S00002.h5 saved, data size: 2398

Run 110 has been saved to file /gpfs/exfel/exp/MID/201901/p002543/scratch/nivanov/hdf5/r0110.h5
Subtracting offsets...
Data shape: (2398, 2, 512, 128)
Done, ADU data shape: (2, 2398, 2, 512, 128)
Baseline correcting...
Done, zero levels: [ -1.18907077 -15.64206141]
Generating mask...
Gain shape: (2398, 2, 512, 128)
Done, mask shape: (2, 2398, 2, 512, 128)
Saving calibrated data to /gpfs/exfel/exp/MID/201901/p002543/scratch/nivanov/hdf5/r0110.h5
```

Or you can batch jobs to generate VDS files to Maxwell cluster:

```
$ python -m vds.batch --help

usage: __main__.py [-h] [--runs RUNS [RUNS ...]] [--config_file CONFIG_FILE]
                   [--calib] [--test]

Batch to Maxwell jobs of creating VDS HDF5

optional arguments:
  -h, --help            show this help message and exit
  --runs RUNS [RUNS ...]
                        run numbers to process
  --config_file CONFIG_FILE
                        Path to ini config file
  --calib               Save calibrated AGIPD data
  --test                Test batching the job to Maxwell

$ python -m vds.batch 109

Submitting job vds_r0109
Shell script: /gpfs/exfel/u/scratch/MID/201901/p002543/nivanov/vds/vds.sh
Command: sbatch --partition upex --job-name vds_r0109 --output /gpfs/exfel/exp/MID/201901/p002543/scratch/nivanov/sbatch_out/vds_r0109_10-25-19_13-49-24.out --error /gpfs/exfel/exp/MID/201901/p002543/scratch/nivanov/sbatch_out/vds_r0109_10-25-19_13-49-24.err /gpfs/exfel/u/scratch/MID/201901/p002543/nivanov/vds/vds.sh /gpfs/exfel/u/scratch/MID/201901/p002543/nivanov 109 --config_file /gpfs/exfel/u/scratch/MID/201901/p002543/nivanov/vds/config.ini --calib
The job vds_r0109 has been submitted
Job ID: 3390425
```

In order to run the package an ini config file is requisite. You can see the example in vds/config.ini. VDS files are saved in "hdf5" folder.