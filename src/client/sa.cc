#include <cmath>
#include <fstream>
#include <sstream>
#include <random>
#include <limits>
#include <vector>

#include <mpi.h>
#include "sa.hpp"
#include "util/timer.hpp"

namespace {
  std::random_device seed;
  std::mt19937 mt(seed());
}

std::vector<float> getPartitionFromParams(const Param& param, int n, int dummy_n) {
  std::vector<float> partition;
  for (int i = 0; i < n; ++i) {
    float x = i - (float) (n-1) / 2;
    float y = param.b * (std::pow(param.a, std::abs(x)) - 1);
    y *= (std::signbit(x)) ? -1 : 1;
    partition.push_back(y);
  }
  while (partition.size() < dummy_n)
    partition.push_back(std::numeric_limits<float>::max());
  return std::move(partition);
}

std::vector<float> getPartitionFromParams(const Param& param, int n) {
  std::vector<float> partition;
  for (int i = 0; i < n; ++i) {
    float x = i - (float) (n-1) / 2;
    float y = param.b * (std::pow(param.a, std::abs(x)) - 1);
    y *= (std::signbit(x)) ? -1 : 1;
    partition.push_back(y);
  }
  return std::move(partition);
}

void SimulatedAnnealing::evaluateState(int n) {
  std::vector<float> tmp;
  tmp.reserve(n*params_.size());
  for (int i = 0; i < params_.size(); ++i) {
    std::vector<float> partition = getPartitionFromParams(params_.at(i), bitwidths_[i], n);
    tmp.insert(tmp.end(), partition.begin(), partition.end());
  }

  MPI_Send(tmp.data(), tmp.size(), MPI_FLOAT, 1, 1, MPI_COMM_WORLD);
  MPI_Recv(&evaluation_, 1, MPI_FLOAT, 1, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
}

void SimulatedAnnealing::updateState_(int n, int layer, int dummy_n) {
  std::uniform_real_distribution<> dist(0, 1.0)
    ;
  /* a, bから代表値(仕切り)の配列を生成 */
  std::vector<float> tmp;
  tmp.reserve(n*params_.size());
  for (int i = 0; i < params_.size(); ++i) {
    std::vector<float> partition = getPartitionFromParams(params_.at(i), bitwidths_[i], dummy_n);
    tmp.insert(tmp.end(), partition.begin(), partition.end());
  }

  /* a, bそれぞれの近傍のを求め、3つのupdate候補を作成 */
  float tmp_a;
  do {
    tmp_a = params_.at(layer).a + (dist(mt) - 0.5) *2 * (1 - params_.at(layer).a)* temperature_;
  } while (tmp_a <= 0);
  float tmp_b = params_.at(layer).b + (dist(mt) - 0.5) * params_.at(layer).b * temperature_;
  std::vector<Param> candidates = {{tmp_a, params_.at(layer).b}, {params_.at(layer).a, tmp_b},
                                   {tmp_a, tmp_b}};
  for (int i = 0; i < (int)candidates.size(); ++i) {
    std::vector<float> partition = getPartitionFromParams(candidates[i], n, dummy_n);
    for (int j = 0; j < n; ++j) {
      tmp[layer*n + j] = partition[j];
    }
    MPI_Send(tmp.data(), tmp.size(), MPI_FLOAT,
             i+1, layer+1, MPI_COMM_WORLD);
  }

  /* Evaluationを受信 */
  for (int i = 0; i < (int)candidates.size(); ++i) {
    float candidate_evl;
    MPI_Recv(&candidate_evl, 1, MPI_FLOAT, i+1, layer+1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    float p = std::exp(-std::abs(candidate_evl- evaluation_)*100 / temperature_);
    if (candidate_evl > evaluation_ || dist(mt) < p) {
      params_.mutable_get().at(layer) = candidates[i];
      evaluation_ = candidate_evl;
    }
  }
}

void SimulatedAnnealing::updateState(int n) {
  for (int i = 0; i < params_.size(); ++i)
      updateState_(bitwidths_[i], i, n);
}

void SimulatedAnnealing::save(std::string filepath) {
  for (int i = 0; i < params_.size(); ++i) {
    std::stringstream filename;
    filename << filepath << "/layer" << i << ".csv";
    std::ofstream ofs(filename.str(), std::ios::app);
    ofs << params_.at(i).a << "," << params_.at(i).b << std::endl;
  }
  std::ofstream ofs(filepath+"/evaluation.csv", std::ios::app);
  ofs << evaluation_ << std::endl;
}

void SimulatedAnnealing::run(int n, std::string filepath) {
  Timer timer;
  timer.start();
  evaluateState(n);
  std::uniform_real_distribution<> dist(0, 1.0);
  int cnt = 0;
  float pre_eval = 0.0;
  while (cnt < 30) {
    updateState(n);
    temperature_ *= cool_down_;
    cnt = (pre_eval == evaluation_) ? cnt + 1 : 0;
    pre_eval = evaluation_;
    save(filepath);
  }
  for (int i = 1; i < 4; ++i) {
    float dummy[n];
    MPI_Send(&dummy, n, MPI_FLOAT, i, 0, MPI_COMM_WORLD);
  }
  timer.show(SEC, "Wall");
}

void gridSearch(int n, std::string filepath) {
  for (int i = 1; i < 100; ++i) {
    std::vector<Param> ps;
    for (int j = 0; j < 4; ++j) {
      for (int k = 0; k < 4; ++k) {
        int rank = j * 4 + k;
        if (rank == 0)
          continue;
        float a = 1.0 + (float)i / 100;
        float b = std::pow(0.1, j) * (1 - 0.25 * k);
        Param p = {a, b};
        ps.push_back(p);
        std::vector<float> partition = getPartitionFromParams(p, n);
        MPI_Send(partition.data(), partition.size(), MPI_FLOAT, rank, 1, MPI_COMM_WORLD);
      }
    }
    std::ofstream ofs(filepath+"/result.csv", std::ios::app);
    for (int j = 1; j < 16; ++j) {
      float eval;
      MPI_Recv(&eval, 1, MPI_FLOAT, j, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
      ofs << ps[j-1].a << "," << ps[j-1].b << "," << eval << std::endl;
    }
    ofs.close();
  }
  for (int i = 1; i < 16; ++i) {
    float dummy[n];
    MPI_Send(&dummy, n, MPI_FLOAT, i, 0, MPI_COMM_WORLD);
  }
}

void saClient(int n, std::string filepath) {
  // std::vector<Param> initial_value = {{1.25, 0.5}, {1.73, 0.075}, {1.82, 0.05},
  //                                     {1.83, 0.025}, {1.75, 0.025}, {1.66, 0.025},
  //                                     {1.8, 0.025}, {1.72, 0.025}, {1.98, 0.01},
  //                                     {1.97, 0.01}, {1.87, 0.01}, {1.53, 0.025},
  //                                     {1.52, 0.025}, {1.34, 0.1}, {1.77, 0.025},
  //                                     {1.31, 0.05}};
  std::vector<Param> initial_value(16, {1.25, 0.05});
  Params init(initial_value);
  SimulatedAnnealing sa(init, 1.0, 0.95);
  std::vector<int> bitwidth(16, n);
  // std::vector<int> bitwidth = {6,5,6,6,7,6,6,6,5,6,6,5,4,2,2,3};
  sa.setBitwidths(bitwidth);
  int tmp[2] = {n, init.size()};
  MPI_Bcast(tmp, 2, MPI_INT, 0, MPI_COMM_WORLD);
  sa.run(n, filepath);
}

// void saClient(int n, std::string filepath) {
//   int t[2] = {n, 1};
//   MPI_Bcast(t, 2, MPI_INT, 0, MPI_COMM_WORLD);
//   gridSearch(n, filepath);
// }
