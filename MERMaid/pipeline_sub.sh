#!/bin/bash
#$ -M  # Email address for job notification
#$ -m abe            # Send mail when job begins, ends and aborts
#$ -q gpu           # Specify queue
#$ -l gpu_card=1
#$ -pe smp 1
#$ -N job_name       # Specify job nam


module load cuda/11.8
module load cudnn/8.9.3
"""
IMPORTANT NOTE:
This is the submission script for  the entirety of C-MAGE.
"""


#Activates the environment we use for VisualHeist-Base and runs its corresponding script
conda activate vh
python3 scripts/run_visualheist.py


#The VisualHeist-Base environment is deactivated and location is transitioned to the DECIMER-Image-Segmentation Directory
conda deactivate
cd ..

#The DECIMER-Image-Segmentation environment is activated and its script is run
cd cxmolscribe-wd/
cd DECIMER-Image-Segmentation/
conda activate ds
python3 pipeline_dis.py

#The DECIMER-Image-Segmentation environment is deactivated and the location is transitioned into the CXMolScribe directory
conda deactivate 
cd ..

#The CXMolScribe environment is activated and its script is run
conda activate 2ms
python3 folder_ms.py
#ALTERNATIVE OPTIPON: If you want the generated CXSMILES not sorted into a seperate High Confidence and Discard Excel files, run the below line instead of the "folder_ms.py" line 
#python3 pipeline_ms.py 


