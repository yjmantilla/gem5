import subprocess
from joblib import Parallel, delayed
import os
BUILDPATH = "build/ARM/gem5.fast"
SCRIPTPATH="configs/CortexA76/CortexA76.py"

WORKLOADS= {
'h264dec':['--cmd=workloads/h264_dec/h264_dec','--options','workloads/h264_dec/h264dec_testfile.264 workloads/h264_dec/h264dec_outfile.yuv'],
'jpeg2k_dec':['--cmd=workloads/jpeg2k_dec/jpg2k_dec','--options','-i workloads/jpeg2k_dec/jpg2kdec_testfile.j2k -o workloads/jpeg2k_dec/jpg2kdec_outfile.bmp'],
'mp3_dec':['--cmd=workloads/mp3_dec/mp3_dec','--options', 'workloads/mp3_dec/mp3dec_outfile.wav workloads/mp3_dec/mp3dec_testfile.mp3'],
'h264_enc':['--cmd=workloads/h264_enc/h264_enc','--options','workloads/h264_enc/h264enc_configfile.cfg'],
'jpeg2k_enc':['--cmd=workloads/jpeg2k_enc/jpg2k_enc','--options','-i workloads/jpeg2k_enc/jpg2kenc_testfile2.bmp -o workloads/jpeg2k_enc/jpg2kenc_outfile.j2k'],
'mp3_enc':['--cmd=workloads/mp3_enc/mp3_enc','--options','workloads/mp3_enc/mp3enc_testfile.wav workloads/mp3_enc/mp3enc_outfile.mp3']
}

workload_iters=['h264dec','jpeg2k_dec']#,'mp3_dec','h264_enc','jpeg2k_enc','mp3_enc']

# Define the command as a list of arguments
from itertools import product

params={
    'l1i_size':['32kB','64kB'],
    'l1d_size':['128kB','256kB'],
}

combinations = list(product(workload_iters,*params.values()))
params.keys()

commands = []
for selwork,*comb in combinations:
    parameters = [f'--{x}={y}' for x,y in zip(params.keys(), comb)]
    namestr = './output/'+'.'.join([f'wl@{selwork}']+[x.replace('=','@').replace('--','') for x in parameters])
    workload=WORKLOADS[selwork]
    command = [
        BUILDPATH,
        f'--outdir={namestr}',
        '--listener-mode=off',
        SCRIPTPATH,
    ] + workload + parameters
    print(command)
    commands.append(command)

import time
def runcommand(cmd):
    start=time.time()
    print(' '.join(cmd))
    out=cmd[1].replace('--outdir=','')
    #print(out)
    os.makedirs(out,exist_ok=True)
    with open(os.path.join(out,"stdout.log"), "w") as outfile, open(os.path.join(out,"stderr.log"), "w") as errfile:
        #print(outfile,errfile)
        try:
            subprocess.run(cmd, stdout=outfile, stderr=errfile, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: The command failed with exit code {e.returncode}")
    end=time.time()
    print(end-start)
    return end-start
print('Num tasks=',len(commands))

n_jobs=2
print('Estimated time',10*len(commands)/n_jobs/60, ' hours')



if n_jobs > 1:
    Parallel(n_jobs=n_jobs)(delayed(runcommand)(cmd) for i,cmd in enumerate(commands))
else:
    for i,cmd in enumerate(commands):
        runcommand(cmd)
    
    

