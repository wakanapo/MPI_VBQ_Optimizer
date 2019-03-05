#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <sstream>
#include <ext/stdio_filebuf.h>
#include <signal.h>

#include <mpi.h>
#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

#include "mpi_to_grpc_communicator.hpp"

#include "protos/genom.pb.h"
#include "protos/genom.grpc.pb.h"
#include "util/util.hpp"

void Communicator::getBufferSize() {
  int tmp[2] = {};
  MPI_Bcast(tmp, 2, MPI_INT, 0, MPI_COMM_WORLD);
  buffer_size_ = tmp[0];
  repeat_times_ = tmp[1];
}

int Communicator::mpiReceiver() {
  arr_.resize(buffer_size_*repeat_times_);
  MPI_Status status;
  MPI_Recv(arr_.data(), buffer_size_*repeat_times_, MPI_FLOAT,
           0, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
  return status.MPI_TAG;
}

int Communicator::grpcSender() {
  GenomEvaluation::Individual individual;
  GenomEvaluation::Genoms genoms;
  for (int i =0; i < repeat_times_; ++i) {
    GenomEvaluation::Genom* genes = genoms.add_genom();
    for (int j = 0; j < buffer_size_; ++j) {
      genes->add_gene(arr_[i*buffer_size_+j]);
    }
  }
  int cnt = 0;
  while(!client_.GetIndividualWithEvaluation(genoms, &individual)) {
    if (cnt == 5) {
      std::cerr << "Tried 5 times, but gRPC Failed." << std::endl;
      return -1;
    }
    ++cnt;
  }
  if (cnt != 0)
    std::cerr << "Success retry." << std::endl;
  val_ = individual.evaluation();
  if (val_ < 0) {
    std::cerr << "Python server catch exception." << std::endl;
    return -1;
  }
  return 0;
}

void Communicator::mpiSender(int tag) {
  MPI_Send(&val_, 1, MPI_FLOAT, 0, tag, MPI_COMM_WORLD);
}

void server(std::string model_name, int quantize_layer, int rank) {
  FILE* fp;
  int p_id;
  std::stringstream command;
  command << "python src/services/genom_evaluation_server.py "
          << model_name << " " << quantize_layer << " " << rank;
  if ((fp = popen2(command.str(), "r", &p_id)) == NULL) {
    std::cerr << "Failed to build server." << std::endl;
    exit(1);
  }
  __gnu_cxx::stdio_filebuf<char> *p_fb =
    new __gnu_cxx::stdio_filebuf<char>(fp, std::ios_base::in);
  std::istream input(static_cast<std::streambuf*>(p_fb));
  std::string line;
  while (!input.eof()) {
    getline(input, line);
    std::cout << line << std::endl;
    if (line == "Server Ready")
      break;
  }
  std::cerr << "Complete buid server." << std::endl;
  int port = 50050 + rank % 4;
  std::string address = "localhost:" + std::to_string(port);
  GenomEvaluationClient client(grpc::CreateChannel(address,
                               grpc::InsecureChannelCredentials()));
  Communicator comm(std::move(client));
  comm.getBufferSize();
  while(pexist(p_id)) {
    int tag = comm.mpiReceiver();
    if (tag == 0)
      break;
    if (comm.grpcSender() < 0) {
      pkill(fp, p_id);
      std::cerr << "Killed server." << std::endl;
      exit(1);
    };
    comm.mpiSender(tag);
  }
  pkill(fp, p_id);
  std::cerr << "Server Finish." << std::endl;
}

