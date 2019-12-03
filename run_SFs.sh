#!/bin/bash

ERA=$1
SUFFIX=$2
INPUT=$3
MVA=$4

./produce_eff_hists.sh $ERA $SUFFIX $INPUT $MVA

./perform_fits.sh $ERA $SUFFIX $MVA

./assemble_efficiencies.sh $ERA $SUFFIX $MVA
