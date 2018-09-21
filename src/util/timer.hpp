#include <chrono>
#include <string>

enum TimeUnit {
  MICROSEC,
  MILLISEC,
  SEC
};

class Timer {
public:
  void start();
  void show(TimeUnit tu, std::string str);
  void save(TimeUnit tu, std::string filename);
private:
  std::chrono::time_point<std::chrono::steady_clock> start_;
};
