#!/bin/bash
# Sort/archive Sentinel-1 data using Apptainer
img=/scale/project/lops-siam-airflow/envs_exploit/apptainer/s1ifr-2026.2.9.sif
cmd='/opt/app-s1ifr/envs/envs1ifr/bin/archivesafe'

linewithoptions="$1 $2 $3 $4"
echo 'options: '$linewithoptions
echo 'command: '$cmd
echo 'img: '$img

apptainer exec \
    --bind /legacy \
    --bind /ontap \
    --bind /scale \
    --bind /scratch \
    $img $cmd $linewithoptions

echo done