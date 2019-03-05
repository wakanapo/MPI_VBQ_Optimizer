#! /bin/sh
#PBS -q l-small
#PBS -l select=1:mpiprocs=4:ompthreads=36
#PBS -W group_list=gj16
#PBS -l walltime=24:00:00

. /etc/profile.d/modules.sh
module load cuda9

export PYENV_ROOT="$PBS_O_WORKDIR/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
if command -v pyenv 1>/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi
eval "$(pyenv virtualenv-init -)"

cd $PBS_O_WORKDIR/MPI_VBQ_Optimizer

export LD_RUN_PATH=/lustre/gj16/j16001/.local/:$LD_RUN_PATH
export LD_LIBRARY_PATH=/lustre/gj16/j16001/.local/lib/:$LD_LIBRARY_PATH
export PATH=/lustre/gj16/j16001/.local/bin/:$PATH

command="mpirun -np 4 ./bin/sa $BITWIDTH vgg16 -1"
echo "$command"
$command

