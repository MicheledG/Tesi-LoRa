#!/bin/bash

#------------------------------------------------------------
#
# Simple script to automate the copy from the repo folder 
# to the "lora_gateway" folder where the source code is compiled
#
# MicheledG 2017-07-19
#
#------------------------------------------------------------

#
# example: ./copy_all_src_code.sh

echo "=================="
echo "Replacing old source code with the new one"

rm -r ~/lora_gateway
mkdir ~/lora_gateway
cd ~/lora_gateway
cp -R ~/Tesi-LoRa/LowCostLoRaGW/gw_full_latest/* .

echo "Done, bye!"
echo "=================="
