#include <iostream>

#include "evaluate_server.hpp"
#include "util/color.hpp"

bool GenomEvaluationClient::
GetIndividualWithEvaluation(const GenomEvaluation::Genom& genom,
                            GenomEvaluation::Individual* individual) {
  grpc::ClientContext context;
  grpc::Status status = stub_->GetIndividual(&context, genom, individual);
  if (!status.ok()) {
    std::cerr << coloringText("ERROR:", RED)
              << "GetIndividual rpc faild." << std::endl;
    return false;
  }
  if (!individual->has_genom()) {
    std::cerr << coloringText("ERROR:", RED)
              << "Server returns incomplete individual." << std::endl;
    return false;
  }
  return true;
}
