#include <string>
#include <vector>

struct Param {
  float a;
  float b;
};

class Params {
public:
  Params(std::vector<Param> params) : v_(params) {};
  const std::vector<Param>& get() {return v_;};
  std::vector<Param>& mutable_get() {return v_;};
  int size() {return v_.size();};
  const Param& at(int i) {return v_[i];};
private:
  float evaluation_(int n, int layer);
  std::vector<Param> v_;
};

class SimulatedAnnealing {
public:
  SimulatedAnnealing(Params params, float temperature, float cool_down) :
    params_(params), evaluation_(0.0), temperature_(temperature), cool_down_(cool_down) {};
  void updateState(int n);
  void run(int n, std::string filepath);
  void save(std::string filepath);
private:
  void updateState_(int n, int layer);
  Params params_;
  float evaluation_;
  float temperature_;
  float cool_down_;
};

void saClient(int n, std::string filepath);
