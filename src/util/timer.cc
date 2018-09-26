#include <iostream>
#include <fstream>

#include "util/timer.hpp"

void Timer::start() {
  start_ = std::chrono::steady_clock::now();
}

void Timer::show(TimeUnit tu, std::string str) {
  auto diff = std::chrono::steady_clock::now() - start_;
  std::cout << str << "Time: ";
  if (tu == MILLISEC)
    std::cout << std::chrono::duration_cast<std::chrono::milliseconds>(diff).count()
              << " millisec.";
  else if (tu == MICROSEC)
    std::cout << std::chrono::duration_cast<std::chrono::microseconds>(diff).count()
              << " microsec.";
  else
    std::cout << std::chrono::duration_cast<std::chrono::seconds>(diff).count()
              << " sec.";
  std::cout << std::endl;
}

void Timer::save(TimeUnit tu, std::string filename) {
  auto diff = std::chrono::steady_clock::now() - start_;
  std::ofstream ofs(filename, std::ios::app);
  ofs << "Time: ";
  if (tu == MILLISEC)
    ofs << std::chrono::duration_cast<std::chrono::milliseconds>(diff).count()
              << " millisec.";
  else if (tu == MICROSEC)
    ofs << std::chrono::duration_cast<std::chrono::microseconds>(diff).count()
              << " microsec.";
  else
    ofs << std::chrono::duration_cast<std::chrono::seconds>(diff).count()
              << " sec.";
  ofs << std::endl;
}
