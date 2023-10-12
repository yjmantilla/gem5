# 1 Run simulations
# from gem5 dir run:

conda deactivate
conda deactivate
python3 design_space_exploration.py > archsim.log

# Generate MCPAT commands

conda deactivate
python3 generate_power_commands.py
cd ..
conda activate py27
cat gem5/powerCommands.sh | parallel -j7

# Intrusction Class Profiling
conda deactivate
conda deactivate
cd gem5
. profile.sh
