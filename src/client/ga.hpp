#pragma once

#include <string>
#include <vector>

using Gene = std::vector<float>;

class Genom {
public:
  Genom(std::vector<Gene> chromosome, float evaluation):
    chromosome_(std::move(chromosome)), evaluation_(evaluation) {
  };
  const std::vector<Gene>& getChromosome() const { return chromosome_; };
  const Gene& getGene(int i) const { return chromosome_[i]; };
  float getEvaluation() const { return evaluation_; };
  float getRandomEvaluation() const { return random_evaluation_; };
  void setChromosome(std::vector<Gene> chromosome) { chromosome_ = chromosome; };
  void setEvaluation(float evaluation) { evaluation_ = evaluation; };
  void setRandomEvaluation(float evaluation);
  void setRandomEvaluation();
private:
  std::vector<Gene> chromosome_;
  float evaluation_;
  float random_evaluation_;
};

class GeneticAlgorithm {
public:
  static GeneticAlgorithm setup(std::string filepath);
  Gene crossover(Gene genom_one, Gene genom_two) const;
  Gene mutation(Gene gene) const;
  void nextGenerationGeneCreate();
  int randomGenomIndex() const;
  void genomEvaluation(int size);
  void run(std::string filename);
  void save(std::string filepath);
  void print(int i, std::string filepath);
  int getGeneLength() {return gene_length_;};
private:
  GeneticAlgorithm(int gene_length, int chrmosome_num, int genom_num, float cross_rate,
                   float mutation_rate, int max_generation)
    : gene_length_(gene_length), chromosome_num_(chrmosome_num), genom_num_(genom_num),
      cross_rate_(cross_rate), mutation_rate_(mutation_rate),
      max_generation_(max_generation) {};
  int gene_length_;
  int chromosome_num_;
  int genom_num_;
  float cross_rate_;
  float mutation_rate_;
  int max_generation_;
  float average_;
  void moveGenoms(std::vector<Genom>&& genom);
  std::vector<Genom> genoms_;
};

void client(std::string filepath);
