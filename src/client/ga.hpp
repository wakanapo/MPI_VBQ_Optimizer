#pragma once
#include "evaluate_server.hpp"

class Genom {
public:
  Genom(std::vector<float> genom_list, float evaluation):
    genom_list_(std::move(genom_list)), evaluation_(evaluation) {
  };
  std::vector<float> getGenom() const { return genom_list_; };
  float getEvaluation() const { return evaluation_; };
  float getRandomEvaluation() const { return random_evaluation_; };
  void setGenom(std::vector<float> genom_list) { genom_list_ = genom_list; };
  void setEvaluation(float evaluation) { evaluation_ = evaluation; };
  void setRandomEvaluation(float evaluation);
  void setRandomEvaluation();
private:
  std::vector<float> genom_list_;
  float evaluation_;
  float random_evaluation_;
};

class GeneticAlgorithm {
public:
  static GeneticAlgorithm setup(std::string filepath);
  std::vector<Genom> crossover(const Genom& mom, const Genom& dad) const;
  Genom mutation(const Genom& parent) const;
  void nextGenerationGeneCreate();
  int randomGenomIndex() const;
  void run(std::string filename, GenomEvaluationClient client);
  void save(std::string filepath);
  void print(int i, std::string filepath);
private:
  GeneticAlgorithm(int genom_length, int genom_num, float cross_rate,
                   float mutation_rate, int max_generation)
    : genom_length_(genom_length), genom_num_(genom_num),
      cross_rate_(cross_rate), mutation_rate_(mutation_rate),
      max_generation_(max_generation) {};
  int genom_length_;
  int genom_num_;
  float cross_rate_;
  float mutation_rate_;
  int max_generation_;
  float average_;
  void moveGenoms(std::vector<Genom>&& genom);
  std::vector<Genom> genoms_;
};
