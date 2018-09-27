#pragma once
#include <vector>

#include "evaluate_server.hpp"

class Communicator {
public:
  Communicator(GenomEvaluationClient client) : client_(std::move(client)) {};
  int mpiReceiver(int buffer_size);
  int grpcSender();
  void mpiSender(int tag);
private:
  std::vector<float> arr_;
  float val_;
  GenomEvaluationClient client_;
};

void server(std::string model_name, int quantize_layer, int genom_length);
