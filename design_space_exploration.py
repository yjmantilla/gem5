import subprocess

# Define the command as a list of arguments
from itertools import product
import os

config_file="configs/learning_gem5/part1/two_level.py"
binary_file="build/X86/gem5.opt"
output_root='output'
params={
    'l2_size':['1MB'],#'2MB'],#,'4MB','8MB'],
    'l1d_size':['128kB'],#,"'256kB'","'512kB'","'1MB'"],
}

combinations = list(product(*params.values()))
params.keys()

commands = []
for comb in combinations:
    parameters = [f'--{x}="{y}"' for x,y in zip(params.keys(), comb)]
    parnames = [f'{x}@{y}' for x,y in zip(params.keys(), comb)]
    namestr = '__'.join(parnames)
    outdir=f"{output_root}/{namestr}"
    os.makedirs(outdir,exist_ok=True)
    command = [
        binary_file,f'--outdir={outdir}',
        config_file,
    ] + parameters
    print(command)
    commands.append(command)


for cmd in commands:

    # Use subprocess to run the command
    try:
        run= ' '.join(cmd[:3])#cmd[:3] #' '.join(cmd
        print(run)	
        result=subprocess.run(run, check=True,shell=True)#,cwd='/home/user/arch/gem5/')
        print('resu',result)
    except subprocess.CalledProcessError as e:
        print(f"Error: The command failed with exit code {e.returncode}")
        print(e)
