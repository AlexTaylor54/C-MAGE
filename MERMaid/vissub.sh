#!/bin/bash
#$ -M  # Email address for job notification
#$ -m abe            # Send mail when job begins, ends and aborts
#$ -q gpu@@wiest_rtx4500a           # Specify queue
#$ -l gpu_card=1
#$ -pe smp 1
#$ -N job_name       # Specify job nam

conda activate vh
module load cuda/11.8
module load cudnn/8.9.3
 
python3 scripts/run_visualheist.py
