#!/bin/bash
# sort WV data
source /usr/share/Modules/3.2.10/init/bash
module load singularity/3.6.4
img=/home/datawork-cersat-public/cache/project/mpc-sentinel1/workspace/singularity/s1ifr/s1ifr.sif
#cmd="micromamba activate /opt/app-s1ifr/envs/envs1ifr && archivesafe -s S1C --mode WV -p OCN_"
#cmd="micromamba activate /opt/app-s1ifr/envs/envs1ifr && archivesafe -h"
#cmd="archivesafe -h"
#cmd='/home1/datahome/agrouaze/sources/git/s1ifr/payload_sorting_S1_product.bash'
cmd='/opt/app-s1ifr/envs/envs1ifr/bin/archivesafe --input-safe '
safe=$1
echo 'safe to sort: '$safe
echo 'command '$cmd
echo 'img '$img
singularity run --bind /home/datawork-cersat-public/ --bind /home1/datahome/ --bind /home1/scratch/ $img $cmd $safe
echo done
