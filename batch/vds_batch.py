import subprocess
import argparse
import os
import numpy as np
from datetime import datetime
from ..config import ConfigParser, CONFIG_PATH, PROJECT_ROOT, SHELL_SCRIPT

MODULES_NUM = 16

class Job(object):
    """
    sbatch job class to create VDS file

    run_number - run number to process
    config - path to config ini file
    proc - flag to process processed files
    calib - flag to save calibrated AGIPD data
    """
    JOB_NAME = "vds_r{:04d}"
    BATCH_CMD = "sbatch"
    SHELL_SCRIPT = SHELL_SCRIPT

    def __init__(self, run_number, config, calib):
        self.run_number, self.config, self.calib = run_number, config, calib
        os.makedirs(self.out_path, exist_ok=True)

    @property
    def job_name(self):
        return self.JOB_NAME.format(self.run_number)

    @property
    def out_path(self):
        return os.path.join(self.config.out_path, 'sbatch_out')

    @property
    def sbatch_params(self):
        now = datetime.now().strftime('%m-%d-%y_%H-%M-%S')
        return ['--partition', 'upex', '--job-name', self.job_name,
                '--output', os.path.join(self.out_path, '{0}_{1}.out'.format(self.job_name, now)),
                '--error', os.path.join(self.out_path, '{0}_{1}.err'.format(self.job_name, now))]

    @property
    def shell_params(self):
        params = [os.path.dirname(PROJECT_ROOT), str(self.run_number)]
        params += ['--config_file', self.config.config_file]
        if self.calib:
            params.append('--calib')
        return params

    @property
    def cmd(self):
        cmd = [self.BATCH_CMD]
        cmd.extend(self.sbatch_params)
        cmd.append(self.SHELL_SCRIPT)
        cmd.extend(self.shell_params)
        return cmd

    def batch(self, test):
        print('Submitting job {}'.format(self.job_name))
        print('Shell script: {}'.format(self.SHELL_SCRIPT))
        print('Command: {}'.format(' '.join(self.cmd)))
        if test:
            return -1
        else:
            try:
                output = subprocess.run(args=self.cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as error:
                err_text = "Command '{}' return with error (code {}): {}".format(' '.join(error.cmd),
                                                                                 error.returncode,
                                                                                 error.stderr)
                raise RuntimeError(err_text) from error
            job_num = int(output.stdout.rstrip().decode("unicode_escape").split()[-1])
            print("The job {0:s} has been submitted".format(self.job_name))
            print("Job ID: {}".format(job_num))
            return job_num

def main():
    parser = argparse.ArgumentParser(description='Batch to Maxwell jobs of creating VDS HDF5')
    parser.add_argument('--runs', nargs='+', type=int, help='run numbers to process')
    parser.add_argument('--config_file', type=str, default=CONFIG_PATH, help="Path to ini config file")
    parser.add_argument('--calib', action="store_true", help="Save calibrated AGIPD data")
    parser.add_argument('--test', action="store_true", help="Test batching the job to Maxwell")
    args = parser.parse_args()

    config = ConfigParser(args.config_file)
    runs = args.runs if args.runs else np.arange(config.run_start, config.run_end)
    for run in runs:
        job = Job(run, config, args.calib)
        job.batch(args.test)
