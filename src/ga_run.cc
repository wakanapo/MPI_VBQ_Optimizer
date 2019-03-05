#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <sys/stat.h>
#include <mpi.h>

#include "client/ga.hpp"
#include "services/mpi_to_grpc_communicator.hpp"
#include "util/flags.hpp"
#include "util/util.hpp"

int main(int argc, char* argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: ./bin/mpi first_genom_file model_name quantize_layer"
              << std::endl;
    return 1;
  }
  Options::ParseCommandLine(argc, argv);
  std::string first_genom_file = argv[1];
  std::string model_name = argv[2];
  int quantize_layer = std::atoi(argv[3]);
  int rank;
  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  if (rank == 0) {
    std::stringstream filepath;
    if (Options::ResumeEnable()) {
      filepath << "data/" << first_genom_file;
    } else {
      filepath << "data/" << model_name << "_"
               << first_genom_file << "_" << quantize_layer << "_" << timestamp();
      mkdir(filepath.str().c_str(), 0777);
    }
    gaClient(filepath.str());
  } else {
    server(model_name, quantize_layer, rank);
  }
  MPI_Finalize();
  return 0;
}
