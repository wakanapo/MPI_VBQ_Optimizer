#include <iostream>

#include "evaluate_server.hpp"
#include "util/color.hpp"
#include "util/flags.hpp"

bool GenomEvaluationClient::
GetIndividualWithEvaluation(const GenomEvaluation::Genoms& genoms,
                            GenomEvaluation::Individual* individual) {
  grpc::ClientContext context;
  grpc::Status status = (Options::IsMock()) ?
    stub_->GetIndividualMock(&context, genoms, individual)
    : stub_->GetIndividual(&context, genoms, individual);
  if (!status.ok()) {
    std::cerr << coloringText("ERROR:", RED)
              << "GetIndividual rpc faild." << std::endl;
    std::cerr << status.error_code() << ": " << status.error_message() << std::endl;
    return false;
  }
  if (!individual->has_genoms()) {
    std::cerr << coloringText("ERROR:", RED)
              << "Server returns incomplete individual." << std::endl;
    return false;
  }
  return true;
}
