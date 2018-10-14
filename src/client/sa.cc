#include <fstream>
#include <sstream>
#include <random>
#include <vector>

#include <mpi.h>
#include "sa.hpp"

namespace {
  std::random_device seed;
  std::mt19937 mt(seed());
}

std::vector<float> getPartitionFromParams(const Param& param, int n) {
  std::vector<float> partition;
  for (int i = 0; i < n; ++i) {
    float x = i / (n-1) - 0.5;
    float y = param.b * (std::pow(param.a, x) - 1);
    y *= (std::signbit(x)) ? -1 : 1;
    partition.push_back(y);
  }
  return std::move(partition);
}

void SimulatedAnnealing::updateState_(int n, int layer) {
  std::uniform_real_distribution<> dist(0, 1.0)
    ;
  /* a, bから代表値(仕切り)の配列を生成 */
  std::vector<float> tmp;
  tmp.reserve(n*params_.size());
  for (auto& param: params_.get()) {
    std::vector<float> partition = getPartitionFromParams(param, n);
    tmp.insert(tmp.end(), partition.begin(), partition.end());
  }

  /* a, bそれぞれの近傍のを求め、3つのupdate候補を作成 */
  float tmp_a = params_.at(layer).a + (dist(mt) - 0.5);
  float tmp_b = params_.at(layer).b + (dist(mt) - 0.5);
  std::vector<Param> candidates = {{tmp_a, params_.at(layer).b}, {params_.at(layer).a, tmp_b},
                                   {tmp_a, tmp_b}};
  for (int i = 0; i < (int)candidates.size(); ++i) {
    std::vector<float> partition = getPartitionFromParams(candidates[i], n);
    for (int j = 0; j < n; ++j) {
      tmp[layer*n + j] = partition[j];
    }
    MPI_Send(tmp.data(), tmp.size(), MPI_FLOAT,
             i, layer+1, MPI_COMM_WORLD);
  }

  /* Evaluationを受信 */
  for (int i = 0; i < (int)candidates.size(); ++i) {
    float candidate_evl;
    MPI_Recv(&candidate_evl, 1, MPI_FLOAT, i, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    float p = std::exp(-std::abs(candidate_evl- evaluation_) / temperature_);
    if (candidate_evl > evaluation_ || dist(mt) < p) {
      params_.mutable_get().at(layer) = candidates[i];
      evaluation_ = candidate_evl;
    }
  }
}

void SimulatedAnnealing::updateState(int n) {
  for (int i = 0; i < params_.size(); ++i) {
    updateState_(n, i);
  }
}

void SimulatedAnnealing::save(std::string filepath) {
  for (int i = 0; i < params_.size(); ++i) {
    std::stringstream filename;
    filename << filepath << "/layer" << i << ".csv";
    std::ofstream ofs(filename.str(), std::ios::app);
    ofs << params_.at(i).a << "," << params_.at(i).b << std::endl;
  }
  std::ofstream ofs(filepath+"/evaluation.csv", std::ios::app);
  ofs << evaluation_ << ",";
}

void SimulatedAnnealing::run(int n, std::string filepath) {
  std::uniform_real_distribution<> dist(0, 1.0);
  while (temperature_ > 0.0001) {
    updateState(n);
    temperature_ *= cool_down_;
    save(filepath);
  }
}

void saClient(int n, std::string filepath) {
  SimulatedAnnealing sa(Params({{100.0, 0.01}}), 10000, 0.99);
  sa.run(n, filepath);
}
