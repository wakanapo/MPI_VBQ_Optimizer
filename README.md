# MPI_VBQ_Optimizer

## How to install

1. install protocol buffers, openmpi
```shell
$ apt install -y protobuf-compiler openmpi-bin libopenmpi-dev
```

2. install requirements by pip

```shell
$ pip install scipy keras tensorflow pillow tqdm
```

3. install gRPC
Please follow instructions: [C++](https://github.com/grpc/grpc/blob/master/BUILDING.md), [Python](https://github.com/grpc/grpc/tree/master/src/python/grpcio)

4. build
```shell
$ make -j20
```

5. create initial set of genoms
```shell
$ mkdir data
$ python src/util/make_first_generation.py 8 50 p8g50 random 
```

6. try running the program with downloading Cifer10
```shell
$ mpirun -n 2 ./bin/mpi p8g50 vgg_like -1
```
