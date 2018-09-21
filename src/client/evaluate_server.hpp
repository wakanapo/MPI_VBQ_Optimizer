#pragma once
#include <memory>
#include <vector>

#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

#include "protos/genom.pb.h"
#include "protos/genom.grpc.pb.h"


class GenomEvaluationClient {
public:
  GenomEvaluationClient(std::shared_ptr<grpc::Channel> channel) :
    stub_(GenomEvaluation::GenomEvaluation::NewStub(channel)) {};
  bool GetIndividualWithEvaluation(const GenomEvaluation::Genom& genom,
                                   GenomEvaluation::Individual* individual);
private:
  std::unique_ptr<GenomEvaluation::GenomEvaluation::Stub> stub_;
};
