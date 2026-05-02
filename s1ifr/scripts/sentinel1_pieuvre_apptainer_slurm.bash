#!/bin/bash
#SBATCH --job-name=archives1safe
#SBATCH --time=10:45:00
#SBATCH --mem=500M
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=%x_%j.log
#SBATCH --error=%x_%j.log

echo 'script to archive Sentinel-1 in Ifremer database '${BASH_SOURCE[0]}

alloptions="$1 $2 $3 $4"
echo "line with options to treat: "$alloptions

# Get the directory of the current script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Construct the full path to the apptainer call script
scriptapptainer="${SCRIPT_DIR}/sentinel1_slurm_apptainer_call.bash"
echo "script to call apptainer image for sorting Sentinel-1 product: "$scriptapptainer

bash $scriptapptainer $alloptions

echo 'end of slurm job to store S1 products in Ifremer database.'
