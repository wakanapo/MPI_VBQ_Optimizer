#! /bin/sh
#PBS -q l-medium
#PBS -l select=8:mpiprocs=4:ompthreads=36
#PBS -W group_list=gj16
#PBS -l walltime=05:00:00

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

if [ $PARAM == "" ]; then
 echo "Please specify the setting param as an environment variable. ex: PARAM=p3g50_4" >&2
 exit 1
fi

settings=$PARAM
echo "== $settings =="
command="mpirun -np 32 ./bin/mpi $settings vgg16 -1"
echo "$command"
$command

