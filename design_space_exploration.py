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

workload_iters=['h264dec','jpeg2k_enc','mp3_enc']#,'mp3_dec','h264_enc','jpeg2k_enc','mp3_enc']

# Define the command as a list of arguments
from itertools import product

params={'l1i_size':["32kB","64kB","128kB"] #"L1 instruction cache size default:""64kB""
#,'l1i_assoc':[4] #"L1 instruction cache associativity default:"4"
#,'l1i_lat':[2] #"L1 instruction cache latency default:"2"
# ,'itb_size':[48] #"Instruction TLB size default:#
#,'l1d_size':["64kB"] #"L1 data cache size default:""64kB""
#,'l1d_assoc':[4,8,16] #"L1 data cache associativity default:"4"
#,'l1d_lat':[4] #"L1 data cache latency default:"4"
# ,'dtb_size':[48] #"Data TLB size default:#
#,'l2_size':["256kB"] #"Unified L2 cache size default:""256kB""
#,'l2_assoc':[8] #"Unified L2 cache associativity default:"8"
,'l2_lat':[6,9,12] #"Unified L2 cache latency default:"9"
,'l3_size':["1MB","2MB","4MB"] #"Shared L3 cache size default:""2MB""
#,'l3_assoc':[16] #"Shared L3 cache associativity default:"16"
#,'l3_lat':[30] #"Shared L3 cache latency default:"30"
#,'fetch_width':[4] #"CPU fetch width default:"4"
#,'decode_width':[4] #"CPU decode width default:"4"
#,'rename_width':[4] #"CPU rename width default:"4"
#,'commit_width':[4] #"CPU commith width default:"4"
#,'dispatch_width':[8] #"CPU dispatch width default:"8"
,'issue_width':[4,8,12] #"CPU issue width default:"8"
#,'wb_width':[4] #"CPU write back width default:"4"
#,'fb_entries':[16] #"Number of fetch buffer entries default:"16"
#,'fq_entries':[16] #"Number of fetch queue entries default:"16"
#,'iq_entries':[16] #"Number of instruction queue entries default:"16"
,'rob_entries':[64,128,256] #"Number of reorder buffer entries default:"128"
#,'lq_entries':[68] #"Number of load queue entries default:"68"
#,'sq_entries':[72] #"Number of store queue entries default:"72"
#,'btb_entries':[8192] #"Number of BTB entries default:"8192"
#,'ras_entries':[16] #"Number of RAS entries default:"16"
#,'num_fu_cmp':[1] #"Number of execution units for compare/branch instructions default:"1"
,'num_fu_intALU':[2,4] #"Number of execution units for integer ALU instructions default:"2"
#,'num_fu_intDIVMUL':[1] #"Number of execution units for integer Division and Multiplication instructions default:"1"
#,'num_fu_FP_SIMD_ALU':[2] #"Number of execution units for Floating-Point and SIMD instructions default:"2"
#,'num_fu_read':[2] #"Number of execution units for load instructions default:"2"
#,'num_fu_write':[1] #"Number of execution units for store instructions default:"1"
#,'branch_predictor_type':[0,3,7] #"Branch predictor type: 0 - BiModeBP, 1 - LTAGE, 2 - LocalBP, 3 - MultiperspectivePerceptron64KB, 4 - MultiperspectivePerceptron8KB, 5 - MultiperspectivePerceptronTAGE64KB, 6 - MultiperspectivePerceptronTAGE8KB, 7 - TAGE, 8 - TAGE_SC_L_64KB, 9 - TAGE_SC_L_8KB, 10 - TournamentBP default:"10"
}

def abbv(x):
    words = x.split("_")
    return ''.join([y[:min(len(y),3)] if i==0 else y.replace('int','')[:min(len(y),1)] for i,y in enumerate(words)])

ABBV_MAP={x:abbv(x) for x in params.keys()}
ABBV_MAP_INV={abbv(x):x for x in params.keys()}


# ojo con variables que no tienen sentido
# cache l1 no deberia ser mas grande que cache l2

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
            end=time.time()
            print(end-start)
            with open(os.path.join(out,f"finished.log"), "w") as outfile:
                outfile.write(f'{end-start}')
        except subprocess.CalledProcessError as e:
            print(f"Error: The command failed with exit code {e.returncode}")

    return None

if __name__=='__main__':
    RUN=True
    combinations = list(product(*params.values(),workload_iters))
    params.keys()

    commands = []
    for *comb,selwork in combinations:
        parameters = [f'--{x}={y}' for x,y in zip(params.keys(), comb)]
        abbvs=[abbv(x) for x in params.keys()]
        namestr = './output/'+'.'.join([f'wl@{selwork}']+[abbvs[i]+'@'+str(comb[i]) for i,x in enumerate(parameters)])
        WORKLOADS_DYNAMIC= {
        'h264dec':[f'--cmd=workloads/h264_dec/h264_dec',f'--options',f'workloads/h264_dec/h264dec_testfile.264 {namestr[2:]}/h264dec_outfile.yuv'],
        'jpeg2k_dec':[f'--cmd=workloads/jpeg2k_dec/jpg2k_dec',f'--options',f'-i workloads/jpeg2k_dec/jpg2kdec_testfile.j2k -o {namestr[2:]}/jpg2kdec_outfile.bmp'],
        'mp3_dec':[f'--cmd=workloads/mp3_dec/mp3_dec',f'--options', f'workloads/mp3_dec/mp3dec_outfile.wav {namestr[2:]}/mp3dec_testfile.mp3'],
        'h264_enc':[f'--cmd=workloads/h264_enc/h264_enc',f'--options',f'workloads/h264_enc/h264enc_configfile.cfg'], #TOFIX, configfile has the output file inside
        'jpeg2k_enc':[f'--cmd=workloads/jpeg2k_enc/jpg2k_enc',f'--options',f'-i workloads/jpeg2k_enc/jpg2kenc_testfile.bmp -o {namestr[2:]}/jpg2kenc_outfile.j2k'],
        'mp3_enc':[f'--cmd=workloads/mp3_enc/mp3_enc',f'--options',f'workloads/mp3_enc/mp3enc_testfile.wav {namestr[2:]}/mp3enc_outfile.mp3']
}
        workload=WORKLOADS_DYNAMIC[selwork]
        workload
        command = [
            BUILDPATH,
            f'--outdir={namestr}',
            '--listener-mode=off',
            SCRIPTPATH,
        ] + workload + parameters
        #print(command)
        if os.path.isfile(os.path.join(namestr[2:],'finished.log')):
            print(os.path.join(namestr[2:],'finished.log'),' already done. Skipping...')
            continue
        commands.append(command)
        

    print('Num tasks=',len(commands))

    n_jobs=10
    print('Estimated time',15*len(commands)/n_jobs/60, ' hours')


    if RUN:
        if n_jobs > 1:
            Parallel(n_jobs=n_jobs)(delayed(runcommand)(cmd) for i,cmd in enumerate(commands))
        else:
            for i,cmd in enumerate(commands):
                runcommand(cmd)
    
    

