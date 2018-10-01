#pragma once
#include <string>

FILE* popen2(std::string command, std::string type, int* pid);
int pclose2(FILE* fp, pid_t pid);
bool pexist(pid_t pid);
int pkill(FILE* fp, pid_t pid);
std::string timestamp();
