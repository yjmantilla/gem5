#! /bin/bash

GEM5PATH=~/gem5/build/ARM
SCRIPTPATH=~/gem5/configs/CortexA76
WORKLOADS=~/gem5/workloads

MOREOPTIONS="--l1i_size=32kB --l1d_size=128kB"

$GEM5PATH/gem5.fast $SCRIPTPATH/CortexA76.py --cmd=$WORKLOADS/jpeg2k_dec/jpg2k_dec --options="-i jpg2kdec_testfile.j2k -o jpg2kdec_outfile.bmp" $MOREOPTIONS
