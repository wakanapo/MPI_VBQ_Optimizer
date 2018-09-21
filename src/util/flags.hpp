#pragma once

#include <string>

class Options {
public:
  static void ParseCommandLine(int argc, char* argv[]);
  static float GetCrossRate();
  static float GetMutationRate();
  static int GetMaxGeneration();
  static bool ResumeEnable();
  static int ResumeFrom();
  static std::string GetFirstGenomFile();
};
