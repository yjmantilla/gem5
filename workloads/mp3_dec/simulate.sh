#! /bin/bash

GEM5PATH=~/gem5/build/ARM
SCRIPTPATH=~/gem5/configs/CortexA76
WORKLOADS=~/gem5/workloads

MOREOPTIONS="--l1i_size=32kB --l1d_size=128kB"

$GEM5PATH/gem5.fast $SCRIPTPATH/CortexA76.py --cmd=$WORKLOADS/mp3_dec/mp3_dec --options="-w mp3dec_outfile.wav mp3dec_testfile.mp3 " $MOREOPTIONS
