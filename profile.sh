seq 1486 | parallel -j 10 --results outputProfile/{} build/ARM/gem5.fast --outdir=outputProfile/i{} configs/learning_gem5/part1/simple-arm.py
