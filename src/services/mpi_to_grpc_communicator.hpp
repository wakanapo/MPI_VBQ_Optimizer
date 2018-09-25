#pragma once
#include <vector>

#include "evaluate_server.hpp"

class Communicator {
public:
  Communicator(GenomEvaluationClient client) : client_(std::move(client)) {};
  int mpiReceiver(int buffer_size);
  void grpcSender();
  void mpiSender(int tag);
private:
  std::vector<float> arr_;
  float val_;
  GenomEvaluationClient client_;
};
