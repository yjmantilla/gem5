#! /bin/bash

GEM5PATH=~/gem5/build/ARM
SCRIPTPATH=~/gem5/configs/CortexA76
WORKLOADS=~/gem5/workloads

MOREOPTIONS="--l1i_size=32kB --l1d_size=128kB"

$GEM5PATH/gem5.fast $SCRIPTPATH/CortexA76.py --cmd=$WORKLOADS/h264_dec/h264_dec --options="h264dec_testfile.264 h264dec_outfile.yuv" $MOREOPTIONS
