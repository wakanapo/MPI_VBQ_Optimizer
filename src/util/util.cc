#include <chrono>
#include <unistd.h>
#include <cstdlib>
#include <cstdio>
#include <csignal>
#include <sys/wait.h>
#include <cerrno>
#include <string>
#include <sstream>
#include <iomanip>

#define READ   0
#define WRITE  1

FILE* popen2(std::string command, std::string type, int* pid) {
  pid_t child_pid;
  int fd[2];
  if (pipe(fd) < 0) {
    perror("pipe");
    exit(1);
  }
  if ((child_pid = fork()) == -1) {
    perror("fork");
    exit(1);
  }

  /* child process */
  if (child_pid == 0) {
    if (type == "r") {
      close(fd[READ]);    //Close the READ end of the pipe since the child's fd is write-only
      dup2(fd[WRITE], 1); //Redirect stdout to pipe
    } else {
      close(fd[WRITE]);    //Close the WRITE end of the pipe since the child's fd is read-only
      dup2(fd[READ], 0);   //Redirect stdin to pipe
    }
    setpgid(0, 0); //Needed so negative PIDs can kill children of /bin/sh
    execl("/bin/sh", "/bin/sh", "-c", command.c_str(), NULL);
    exit(0);
  } else {
    if (type == "r") {
      close(fd[WRITE]); //Close the WRITE end of the pipe since parent's fd is read-only
    } else {
      close(fd[READ]); //Close the READ end of the pipe since parent's fd is write-only
    }
  }
  *pid = child_pid;
  if (type == "r")
    return fdopen(fd[READ], "r");
  return fdopen(fd[WRITE], "w");
}

int pclose2(FILE* fp, pid_t pid) {
  int stat;
  fclose(fp);
  while (waitpid(pid, &stat, 0) == -1) {
    if (errno != EINTR) {
      stat = -1;
      break;
    }
  }
  return stat;
}

int pkill(FILE* fp, pid_t pid) {
  int stat;
  fclose(fp);
  killpg(getpgid(pid), SIGINT);
  while (waitpid(pid, &stat, 0) == -1) {
    if (errno != EINTR) {
      stat = -1;
      break;
    }
  }
  return stat;
}

std::string timestamp() {
  std::time_t t = time(NULL);
  const tm* lt = localtime(&t);
  std::stringstream ss;
  ss << std::setw(2) << std::setfill('0') << lt->tm_mon+1;
  ss << std::setw(2) << std::setfill('0') << lt->tm_mday;
  ss << std::setw(2) << std::setfill('0') << lt->tm_hour;
  ss << std::setw(2) << std::setfill('0') << lt->tm_min;
  ss << std::setw(2) << std::setfill('0') << lt->tm_sec;
  return ss.str();
}
