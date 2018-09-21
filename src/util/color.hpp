#pragma once
#include <cstdlib>
#include <sstream>

enum Color {
  BLACK,
  RED,
  GREEN,
  YELLOW,
  BLUE,
  MAGENTA,
  CYAN,
  WHITE,
  DUMMY,
  NORMAL,
};

std::string coloringText(std::string str, Color c);
