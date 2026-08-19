#!/bin/bash
#
# Submit the whole C-MAGE pipeline to SGE, on a node with a GPU.
#
# Run this from the repository root:
#
#   qsub MERMaid/pipeline_sub.sh
#   qsub MERMaid/pipeline_sub.sh --pdfs /path/to/papers --separated no
#
# Arguments are passed through to run_pipeline.sh unchanged.
#
# Login nodes have no GPU, so running run_pipeline.sh directly there falls
# back to CPU. Submitting is what gets you onto a GPU node.
#
# Add your own address if you want mail:  #$ -M you@nd.edu  and  #$ -m abe
#
#$ -q gpu
#$ -l gpu_card=1
#$ -pe smp 1
#$ -N cmage
#$ -cwd
#$ -j y

module load cuda/11.8
module load cudnn/8.9.3

# Stages detect CUDA themselves, so nothing else has to be set here.
exec ./run_pipeline.sh "$@"
