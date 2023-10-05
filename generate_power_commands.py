# execute this file from arch/gem5/
import os
import glob
import pandas as pd
    
DATAPATTERN='output/**/stats.txt'
DATAPATH='output'

PALL= True


files=glob.glob(DATAPATTERN,recursive=True)
print(files)

def get_command(ff):
	stats=ff
	cfg=stats.replace('stats.txt','config.json')
	xml=stats.replace('stats.txt','config.xml')
	power=stats.replace('stats.txt','power.log')

	# to be run from arch dir (the root of gem5 and mcpat)
	command1=f'python gem5/gem5toMcPAT_cortexA76.py gem5/{stats} gem5/{cfg} gem5/ARM_A76_2.1GHz.xml gem5/{xml}'
	command2=f'./mcpat/mcpat -infile gem5/{xml} > gem5/{power}'

	return [command1,command2]

commands =[]

for ff in files:
	if not PALL:
		commands += get_command(ff)
	else:
		a,b=get_command(ff)
		commands+=['(',a,b+' ) &']
commands+=['pwd']
print(commands)
#commands=['conda activate py27']+commands
with open('powerCommands.sh', 'w') as f:
    for line in commands:
        f.write(f"{line}\n")

# after that from root
# sudo chmod -R +x *
# conda activate py27
# . gem5/powerCommands.sh > pall.log

# if parallel
# sudo apt install parallel
