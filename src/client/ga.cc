#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <future>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <thread>
#include <vector>

#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

#include "ga.hpp"
#include "util/color.hpp"
#include "util/flags.hpp"
#include "util/timer.hpp"
#include "protos/genom.pb.h"
#include "protos/genom.grpc.pb.h"

std::random_device seed;
std::mt19937 mt(seed());

void Genom::setRandomEvaluation() {
  std::uniform_real_distribution<> rand(0.0, evaluation_);
  random_evaluation_ = rand(mt);
}

void Genom::setRandomEvaluation(float evaluation) {
  random_evaluation_ = evaluation;
}

GeneticAlgorithm GeneticAlgorithm::setup(std::string filepath) {
  GenomEvaluation::Generation generation;
  std::fstream input(Options::GetFirstGenomFile(),
                     std::ios::in | std::ios::binary);
  if (!generation.ParseFromIstream(&input)) {
    std::cerr << "Cannot load first genoms." << std::endl;
    exit(1);
  }

  GeneticAlgorithm ga(generation.individuals(0).genom().gene_size() ,
                      generation.individuals_size(),
                      Options::GetCrossRate(),Options::GetMutationRate(),
                      Options::GetMaxGeneration());

  if (!Options::ResumeEnable()) {
    std::ofstream ofs(filepath+"/metadata.txt", std::ios::app);
    ofs << "Genom Length: " << ga.genom_length_ << std::endl;
    ofs << "The number of Genom: " << ga.genom_num_ << std::endl;
    ofs << "Crossover Rate: " << ga.cross_rate_ << std::endl;
    ofs << "Mutation Rate: " << ga.mutation_rate_ << std::endl;
    ofs << "The number of Generaion: " << ga.max_generation_ << std::endl;
  }
  
  std::vector<Genom> genoms;
  for (int i = 0; i < generation.individuals_size(); ++i) {
    std::vector<float> gene;
    for (int j = 0; j < generation.individuals(0).genom().gene_size(); ++j) {
      gene.push_back(generation.individuals(i).genom().gene(j));
    }
    genoms.push_back({gene, generation.individuals(i).evaluation()});
  }
  ga.moveGenoms(std::move(genoms));
  return ga;
}

void GeneticAlgorithm::moveGenoms(std::vector<Genom>&& genoms) {
  genoms_ = std::move(genoms);
}

std::vector<Genom> GeneticAlgorithm::crossover(const Genom& mom, const Genom& dad) const {
  /*
    二点交叉を行う関数
  */
  // 両端はcenterに選ばない
  std::uniform_int_distribution<> dist(1, genom_length_-2);
  int center = dist(mt);
  int range = std::min({(dist(mt)+1)/2, center, (genom_length_ - center)});
  std::vector<float> genom_one = mom.getGenom();
  std::vector<float> genom_two = dad.getGenom();
  auto inc_itr = std::lower_bound(genom_two.begin(), genom_two.end(),
                                  genom_one[center]);
  auto dic_itr = inc_itr;
  dic_itr--;
  for (int i = 0; i < range; ++i) {
    if (inc_itr != genom_two.end()) {
      std::swap(*inc_itr, genom_one[center+i]);
      ++inc_itr;
    }

    // i = 0 の時こちらもgenom_one[center]とswapしてしまうので i = 0は除外
    if (i != 0 && dic_itr >= genom_two.begin()) {
      std::swap(*dic_itr, genom_one[center-i]);
      --dic_itr;
    }
  }
  std::sort(genom_one.begin(), genom_one.end());
  std::sort(genom_two.begin(), genom_two.end());
  return {{genom_one, 0}, {genom_two, 0}};
}

Genom GeneticAlgorithm::mutation(const Genom& parent) const {
  /*
    突然変異関数
  */
  std::uniform_real_distribution<> rand(0.0, 1.0);
  std::vector<float> genes = parent.getGenom();
  
  for (int i = 0; i < genom_length_; ++i) {
    float left = (i == 0) ? genes[i] - 0.05 : genes[i-1];
    float right = (i == genom_length_ - 1) ? genes[i] + 0.05 : genes[i+1];
    std::uniform_real_distribution<> new_pos(left, right);
    genes[i] = new_pos(mt);
  }
  return {genes, 0};
}

int maxGenom(std::vector<Genom> genoms) {
  int max_i = 0;
  float max_v = genoms[0].getEvaluation();
  for (uint i = 0; i < genoms.size(); ++i) {
    if (genoms[i].getEvaluation() >  max_v) {
      max_i = i;
      max_v = genoms[i].getEvaluation();
    }
  }
  return max_i;
}


void GeneticAlgorithm::nextGenerationGeneCreate() {
  /*
    世代交代処理を行う関数
  */
  int max_idx = maxGenom(genoms_);
  genoms_[max_idx].setRandomEvaluation(genoms_[max_idx].getEvaluation());
  
  std::sort(genoms_.begin(), genoms_.end(),
            [](const Genom& a, const Genom& b) {
              return a.getRandomEvaluation() > b.getRandomEvaluation();
            });

  std::uniform_real_distribution<> rand(0.0, mutation_rate_ + cross_rate_);
  std::vector<Genom> new_genoms;
  new_genoms.reserve(genom_num_);
  
  int reproduce_genom_num = (int) genom_num_ * (1 - mutation_rate_ - cross_rate_);
  for (int i = 0; i < reproduce_genom_num; ++i)
    new_genoms.push_back(genoms_[i]);

  std::uniform_int_distribution<> dist(0, genom_num_-1);

  while ((int)new_genoms.size() < genom_num_) {
    int idx = dist(mt);
    auto r = rand(mt);
    // /* 選択 */
    // if (r > mutation_rate_ + cross_rate_) {
    //   new_genoms.push_back(genoms_[idx]);
    //   continue;
    // }

    /* 突然変異 */
    if (r < mutation_rate_) {
      new_genoms.push_back(mutation(genoms_[idx]));
      continue;
    }

    /* 交叉 */
    if ((int)new_genoms.size() <= genom_num_ - 2) {
      int idx2 = dist(mt);
      while (idx2 == idx) {
        idx2 = dist(mt);
      }
      auto genoms = crossover(genoms_[idx], genoms_[idx2]);
      std::copy(genoms.begin(), genoms.end(), std::back_inserter(new_genoms));
      continue;
    }
  }
  genoms_ = std::move(new_genoms);
}

int GeneticAlgorithm::randomGenomIndex() const{
  std::uniform_real_distribution<> rand(0.0, 1.0);
  float r = rand(mt);
  for (int i = 0; i < genom_num_; ++i) {
    float ratio = genoms_[i].getEvaluation() / (average_ * genom_num_);
    if (r < ratio)
      return i;
    r -= ratio;
  }
  return std::rand() % genom_num_;
}

void GeneticAlgorithm::print(int i, std::string filepath) {
  float min = 1.0;
  float max = 0;
  float sum = 0;
  
  for (auto& genom: genoms_) {
    float evaluation = genom.getEvaluation();
    sum += evaluation;
    if (evaluation < min)
      min = evaluation;
    if (evaluation > max)
      max = evaluation;
  }
  average_ = sum / genom_num_;

  std::ofstream ofs(filepath+"/log.txt", std::ios::app);
  ofs << "generation: " << i << std::endl;
  ofs << "Min: " << min << std::endl;
  ofs << "Max: " << max << std::endl;
  ofs << "Ave: " << average_ << std::endl;
  ofs << "-------------" << std::endl;
}

void GeneticAlgorithm::save(std::string filename) {
  GenomEvaluation::Generation gs;
  for (auto genom : genoms_) {
    GenomEvaluation::Individual* g = gs.add_individuals();
    GenomEvaluation::Genom* genes = new GenomEvaluation::Genom();
    for (auto gene : genom.getGenom()) {
      genes->mutable_gene()->Add(gene);
    }
    g->set_allocated_genom(genes);
    g->set_evaluation(genom.getEvaluation());
  }

  std::fstream output(filename+".pb",
                      std::ios::out | std::ios::trunc | std::ios::binary);
  if (!gs.SerializeToOstream(&output))
    std::cerr << "Failed to save genoms." << std::endl;
}

void GeneticAlgorithm::run(std::string filepath, GenomEvaluationClient client) {
  Timer timer;
  for (int i = Options::ResumeFrom();
       i < Options::ResumeFrom() + max_generation_; ++i) {
    timer.start();
    if (Options::ResumeEnable() || i != 0) {
      /* 次世代集団の作成 */
      std::cerr << "Creating next generation ..... ";
      nextGenerationGeneCreate();
      std::cerr << coloringText("OK!", GREEN) << std::endl;
    }

    std::cerr << "Evaluating genoms on server ..... " << std::endl;
    for (Genom& genom: genoms_) {
      if (genom.getEvaluation() <= 0) {
        GenomEvaluation::Individual individual;
        GenomEvaluation::Genom* genes = new GenomEvaluation::Genom();
        for (auto gene : genom.getGenom()) {
          genes->mutable_gene()->Add(gene);
        }
        client.GetIndividualWithEvaluation(*genes, &individual);
        genom.setEvaluation(individual.evaluation());
      }
      genom.setRandomEvaluation();
    }
    std::cerr << coloringText("Finish Evaluation!", GREEN) << std::endl;

    std::cerr << "Saving generation data ..... ";
    std::stringstream ss;
    ss << std::setw(3) << std::setfill('0') << i;
    save(filepath+"/generation"+ss.str());
    std::cerr << coloringText("OK!", GREEN) << std::endl;
    print(i, filepath);
    timer.show(SEC, "Generation" + std::to_string(i) + "\n");
    timer.save(SEC, filepath+"/log.txt");
  }
}

std::string timestamp() {
  std::time_t t = time(NULL);
  const tm* lt = localtime(&t);
  std::stringstream ss;
  ss << std::setw(2) << std::setfill('0') << lt->tm_mon+1;
  ss << std::setw(2) << std::setfill('0') << lt->tm_mday;
  ss << std::setw(2) << std::setfill('0') << lt->tm_hour;
  ss << std::setw(2) << std::setfill('0') << lt->tm_min;
  ss << std::setw(2) << std::setfill('0') << lt->tm_sec;
  return ss.str();
}

int main(int argc, char* argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: ./bin/ga first_genom_file model_name quantize_layer" << std::endl;
    return 1;
  }
  Options::ParseCommandLine(argc, argv);
  std::stringstream filepath;
  if (Options::ResumeEnable()) {
    filepath << "data/" << argv[1];
  } else {
    filepath << "data/" << argv[2] << "_" << argv[1] << "_"<< argv[3] << "_" << timestamp();
    mkdir(filepath.str().c_str(), 0777);
  }
  
  GeneticAlgorithm ga = GeneticAlgorithm::setup(filepath.str());
  GenomEvaluationClient client(
    grpc::CreateChannel("localhost:50051",
                        grpc::InsecureChannelCredentials()));
  ga.run(filepath.str(), std::move(client));
}
