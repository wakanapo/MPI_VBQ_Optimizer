#pragma once
#include <vector>

#include "evaluate_server.hpp"

class Communicator {
public:
  Communicator(GenomEvaluationClient client) : buffer_size_(1000), repeat_times_(1),
                                               client_(std::move(client)) {};
  int mpiReceiver();
  int grpcSender();
  void mpiSender(int tag);
  void getBufferSize();
private:
  int buffer_size_;
  int repeat_times_;
  std::vector<float> arr_;
  float val_;
  GenomEvaluationClient client_;
};

void server(std::string model_name, int quantize_layer, int rank);
