#!/bin/bash
#$ -M ataylo29@nd.edu # Email address for job notification
#$ -m abe            # Send mail when job begins, ends and aborts
#$ -q gpu           # Specify queue
#$ -l gpu_card=1
#$ -pe smp 1
#$ -N job_name       # Specify job nam

conda activate 2ms #changed to make it cx

module load cuda/11.8
module load cudnn/8.9.3

python3 analyze_ds3.py


