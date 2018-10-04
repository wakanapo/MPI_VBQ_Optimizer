#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <future>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <sys/stat.h>
#include <thread>

#include <mpi.h>

#include "ga.hpp"
#include "util/color.hpp"
#include "util/flags.hpp"
#include "util/timer.hpp"
#include "protos/genom.pb.h"

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

  GeneticAlgorithm ga(generation.individuals(0).genoms().genom(0).gene_size() ,
                      generation.individuals(0).genoms().genom_size(),
                      generation.individuals_size(),
                      Options::GetCrossRate(),Options::GetMutationRate(),
                      Options::GetMaxGeneration());
  int tmp[2] = {ga.gene_length_, ga.chromosome_num_};
  MPI_Bcast(tmp, 2, MPI_INT, 0, MPI_COMM_WORLD);
  if (!Options::ResumeEnable()) {
    std::ofstream ofs(filepath+"/metadata.txt", std::ios::app);
    ofs << "Gene Length: " << ga.gene_length_ << std::endl;
    ofs << "The number of Chromosome: " << ga.chromosome_num_ << std::endl;
    ofs << "The number of Genom: " << ga.genom_num_ << std::endl;
    ofs << "Crossover Rate: " << ga.cross_rate_ << std::endl;
    ofs << "Mutation Rate: " << ga.mutation_rate_ << std::endl;
    ofs << "The number of Generaion: " << ga.max_generation_ << std::endl;
  }
  
  std::vector<Genom> genoms;
  for (int i = 0; i < generation.individuals_size(); ++i) {
    std::vector<Gene> chronosome;
    for (int j = 0; j < generation.individuals(0).genoms().genom_size(); ++j) {
      Gene gene;
      for (int k = 0; k < generation.individuals(0).genoms().genom(j).gene_size(); ++k) {
        gene.push_back(generation.individuals(i).genoms().genom(j).gene(k));
      }
      chronosome.push_back(gene);
    }
    genoms.push_back({chronosome, generation.individuals(i).evaluation()});
  }
  ga.moveGenoms(std::move(genoms));
  return ga;
}

void GeneticAlgorithm::moveGenoms(std::vector<Genom>&& genoms) {
  genoms_ = std::move(genoms);
}

Gene GeneticAlgorithm::crossover(Gene genom_one, Gene genom_two) const {
  /*
    二点交叉を行う関数
  */
  // 両端はcenterに選ばない
  std::uniform_int_distribution<> dist(1, gene_length_-2);
  int center = dist(mt);
  int range = std::min({(dist(mt)+1)/2, center, (gene_length_ - center)});
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
  return genom_one;
}

Gene GeneticAlgorithm::mutation(Gene gene) const {
  /*
    突然変異関数
  */
  std::uniform_real_distribution<> rand(0.0, 1.0);
  
  for (int i = 0; i < gene_length_; ++i) {
    float left = (i == 0) ? gene[i] - 0.05 : gene[i-1];
    float right = (i == gene_length_ - 1) ? gene[i] + 0.05 : gene[i+1];
    std::uniform_real_distribution<> new_pos(left, right);
    gene[i] = new_pos(mt);
  }
  return gene;
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

  /* 再生 */
  int reproduce_genom_num = (int) genom_num_ * (1 - mutation_rate_ - cross_rate_);
  for (int i = 0; i < reproduce_genom_num; ++i)
    new_genoms.push_back(genoms_[i]);

  std::uniform_int_distribution<> dist(0, genom_num_-1);

  while ((int)new_genoms.size() < genom_num_) {
    int idx = dist(mt);
    std::vector<Gene> new_genom;

    for (int i = 0; i < chromosome_num_; ++i) {
      const Gene& gene = genoms_[idx].getGene(i);
      auto r = rand(mt);
      /* 突然変異 */
      if (r < mutation_rate_) {
        new_genom.push_back(mutation(gene));
        continue;
      }

      r -= mutation_rate_;
      /* 交叉 */
      if (r < cross_rate_) {
        int idx2 = dist(mt);
        while (idx2 == idx) {
          idx2 = dist(mt);
        }
        new_genom.push_back(crossover(gene, genoms_[idx2].getGene(i)));
        continue;
      }
      /* 再生 */
    }

    new_genoms.push_back({new_genom, 0});
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

void GeneticAlgorithm::genomEvaluation(int size) {
  int node = 0;
  std::vector<std::pair<int, int>> targets;
  /* Genomを送信 */
  for (int g_id = 0; g_id < genom_num_; ++g_id) {
    const Genom& genom = genoms_[g_id];
    std::vector<float> tmp(gene_length_*chromosome_num_);
    for (auto& gene : genom.getChromosome()) {
      tmp.insert(tmp.end(), gene.begin(), gene.end());
    }
    if (genom.getEvaluation() <= 0) {
      int target_rank = node % (size-1) + 1;
      MPI_Send(tmp.data(), gene_length_*chromosome_num_, MPI_FLOAT,
               target_rank, g_id+1, MPI_COMM_WORLD);
      targets.push_back({target_rank, g_id});
      ++node;
    }
  }
  /* Evaluationを受信 */
  for (const auto& t : targets) {
    float evaluation;
    MPI_Recv(&evaluation, 1, MPI_FLOAT, t.first, t.second+1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    genoms_[t.second].setEvaluation(evaluation);
  }
  /* RandomEvaluationをセット */
  for (Genom& genom : genoms_) {
    genom.setRandomEvaluation();
  }
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
  if (Options::IsMock()) {
    for (auto genom : genoms_) {
      if (genom.getEvaluation() != 0.5) {
        std::cout << coloringText("Mock Failed!", RED) << std::endl;
        return;
      }
    }
    std::cout << coloringText("Mock Success!", GREEN) << std::endl;
    return;
  }
  
  GenomEvaluation::Generation gs;
  for (auto& genom : genoms_) {
    GenomEvaluation::Individual* g = gs.add_individuals();
    GenomEvaluation::Genoms* genoms = new GenomEvaluation::Genoms();
    for (auto& gene : genom.getChromosome()) {
      GenomEvaluation::Genom* genes = genoms->add_genom();
      for (float v : gene) {
        genes->add_gene(v);
      }
    }
    g->set_allocated_genoms(genoms);
    g->set_evaluation(genom.getEvaluation());
  }

  std::fstream output(filename+".pb",
                      std::ios::out | std::ios::trunc | std::ios::binary);
  if (!gs.SerializeToOstream(&output))
    std::cerr << "Failed to save genoms." << std::endl;
}

void GeneticAlgorithm::run(std::string filepath) {
  int size;
  MPI_Comm_size(MPI_COMM_WORLD, &size);
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
    /* 遺伝子の評価 */
    std::cerr << "Evaluating genoms on server ..... " << std::endl;
    genomEvaluation(size);
    std::cerr << coloringText("Finish Evaluation!", GREEN) << std::endl;
    /* 保存 */
    std::cerr << "Saving generation data ..... ";
    std::stringstream ss;
    ss << std::setw(3) << std::setfill('0') << i;
    save(filepath+"/generation"+ss.str());
    std::cerr << coloringText("OK!", GREEN) << std::endl;
    
    print(i, filepath);
    timer.show(SEC, "Generation" + std::to_string(i) + "\n");
    timer.save(SEC, filepath+"/log.txt");
  }
  /* Server Shutdown */
  float dummy = 0.0;
  for (int i = 1; i < size; ++i) {
    MPI_Send(&dummy, 1, MPI_FLOAT,
             i, 0, MPI_COMM_WORLD);
  }
  std::cerr << "Client Finish." << std::endl;
}

void client(std::string filepath){
  GeneticAlgorithm ga = GeneticAlgorithm::setup(filepath);
  ga.run(filepath);
}
