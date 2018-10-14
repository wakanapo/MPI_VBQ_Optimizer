#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <sys/stat.h>
#include <mpi.h>

#include "client/sa.hpp"
#include "services/mpi_to_grpc_communicator.hpp"
#include "util/flags.hpp"
#include "util/util.hpp"

int main(int argc, char* argv[]) {
  if (argc < 3) {
    std::cerr << "Usage: ./bin/sa partition_num  model_name"
              << std::endl;
    return 1;
  }
  int n = std::atoi(argv[1]);
  std::string model_name = argv[2];
  int rank;
  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  if (rank == 0) {
    std::stringstream filepath;
    filepath << "data/" << model_name << "_" << n << "_" << timestamp();
    mkdir(filepath.str().c_str(), 0777);
    saClient(n, filepath.str());
  } else {
    server(model_name, -1, rank);
  }
  MPI_Finalize();
  return 0;
}