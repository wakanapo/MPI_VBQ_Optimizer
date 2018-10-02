#include <iostream>
#include <iomanip>
#include <map>
#include <string>
#include <sstream>

#include "util/flags.hpp"

typedef std::map<std::string, void(*)(std::string)> flags_type;

namespace {
  float g_mutation_rate = 0.2;
  float g_cross_rate = 0.5;
  int g_max_generation = 200;
  bool g_resume = false;
  int g_resume_from = 0;
  std::string g_first_genom_file;
  bool g_is_mock = false;
}  // namespace

int StringToInt(std::string str) {
  return std::stoi(str);
}

float StringToFloat(std::string str) {
  return std::stof(str);
}

bool StringToBool(std::string str) {
  return (str == "true") ? true : false;
}

void SetFlag(std::string str, flags_type& flags) {
  std::string::size_type equal_pos = str.find("=");
  if (equal_pos == std::string::npos || (str[0] != '-' && str[1] != '-')) {
    std::cerr << "Flag Syntax Error: Cannot parse flags." << std::endl;
    std::cerr << "===Usage===\n ./bin/cnn MODE --flag1=hoge --flag2==fuga" << std::endl;
    exit(1);
  }
  std::string flag_name = std::string(str.begin() + 2, str.begin() + equal_pos);
  std::string flag_value = std::string(str.begin() + equal_pos + 1, str.end());

  flags_type::iterator it = flags.find(flag_name);
  if (it == flags.end()) {
    std::cerr << "Unknown Flag: \'" << flag_name << "\' is undefined." << std::endl;
  } else {
    it->second(flag_value);
  }
};

void Options::ParseCommandLine(int argc, char* argv[]) {
    if (argc < 4) {
    std::cerr << "Usage: ./bin/mpi first_genom_file model_name quantize_layer"
              << std::endl;
    exit(1);
  }

  flags_type flags;
  flags.insert(std::make_pair("cross_rate", [](std::string flag_value) {
        g_cross_rate = StringToFloat(flag_value); }));
  flags.insert(std::make_pair("mutation_rate", [](std::string flag_value) {
        g_mutation_rate = StringToFloat(flag_value); }));
  flags.insert(std::make_pair("max_generation", [](std::string flag_value) {
        g_max_generation = StringToInt(flag_value);}));
  flags.insert(std::make_pair("resume_from", [](std::string flag_value) {
        g_resume = true;
        g_resume_from = StringToInt(flag_value);}));
  flags.insert(std::make_pair("is_mock", [](std::string flag_value) {
        g_is_mock = StringToBool(flag_value) ;}));
  for (int i = 4; i < argc; ++i)
    SetFlag(argv[i], flags);
  std::stringstream filename;
  if (g_resume) {
    filename << "data/" << argv[1] << "/generation" <<
      std::setw(3) << std::setfill('0') << g_resume_from-1 << ".pb";
  } else {
    filename << "data/" << argv[1] << ".pb";
  }
  g_first_genom_file = filename.str();
}

float Options::GetCrossRate() {
  return g_cross_rate;
}

float Options::GetMutationRate() {
  return g_mutation_rate;
}

int Options::GetMaxGeneration() {
  return g_max_generation;
}

bool Options::ResumeEnable() {
  return g_resume;
}

int Options::ResumeFrom() {
  return g_resume_from;
}

std::string Options::GetFirstGenomFile() {
  return g_first_genom_file;
}

bool Options::IsMock() {
  return g_is_mock;
}
