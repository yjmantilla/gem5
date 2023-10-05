#! /bin/bash

GEM5PATH=~/gem5/build/ARM
SCRIPTPATH=~/gem5/configs/CortexA76
WORKLOADS=~/gem5/workloads

MOREOPTIONS="--l1i_size=32kB --l1d_size=128kB"

$GEM5PATH/gem5.fast $SCRIPTPATH/CortexA76.py --cmd=$WORKLOADS/jpeg2k_enc/jpg2k_enc --options="-i jpg2kenc_testfile2.bmp -o jpg2kenc_outfile.j2k" $MOREOPTIONS
