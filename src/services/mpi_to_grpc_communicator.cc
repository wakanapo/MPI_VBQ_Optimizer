#include <iostream>

#include <mpi.h>
#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

#include "mpi_to_grpc_communicator.hpp"

#include "protos/genom.pb.h"
#include "protos/genom.grpc.pb.h"

int Communicator::mpiReceiver(int buffer_size) {
  arr_.resize(buffer_size);
  MPI_Status status;
  MPI_Recv(arr_.data(), buffer_size, MPI_FLOAT,
           0, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
  return status.MPI_TAG;
}

void Communicator::grpcSender() {
  GenomEvaluation::Individual individual;
  GenomEvaluation::Genom* genes = new GenomEvaluation::Genom();
  for (float v : arr_) {
    genes->mutable_gene()->Add(v);
  }
  client_.GetIndividualWithEvaluation(*genes, &individual);
  val_ = individual.evaluation();
}

void Communicator::mpiSender(int tag) {
  MPI_Send(&val_, 1, MPI_FLOAT, 0, tag, MPI_COMM_WORLD);
}

int main(int argc, char* argv[]) {
  if (argc < 2) {
    std::cerr << "Usage: ./server <genom_length>" << std::endl;
    exit(1);
  }
  MPI_Init(&argc, &argv);
  GenomEvaluationClient client(grpc::CreateChannel("localhost:50051",
                               grpc::InsecureChannelCredentials()));
  Communicator comm(std::move(client));
  while(1) {
    int tag = comm.mpiReceiver(std::atoi(argv[1]));
    if (tag == 0)
      break;
    comm.grpcSender();
    comm.mpiSender(tag);
  }
  MPI_Finalize();
}
