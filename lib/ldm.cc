#include "ldm.h"

int ServiceManager::LoadService(std::initializer_list<const char*> names) {
  int res = 0;
  for (const auto &n : names) {
    std::unordered_map<std::string, Service*>::iterator it = services_.find(n);
    if (it == services_.end()) {
      void *handle = dlopen(n, RTLD_NOW);
      if (!handle) {
        std::cerr << "Failed to open " << n << std::endl;
        return -1;
      }
      GetServiceFunc get_service = nullptr;
      *(void**)(&get_service) = dlsym(handle, "get_service");
      if (!get_service) {
        std::cerr << "please export get_service function." << std::endl;
        return -1;
      }
      Service *s = get_service();
      s->start();
      services_.insert({n, s});
      res++;
      std::cout << "load " << n << " success" << std::endl;
    }
  }
  return res;
}
int ServiceManager::ReloadService(std::initializer_list<const char*> names) {
  for (const auto &n : names) {
    UnloadService({n});
    LoadService({n});
  }
  return names.size();
}
int ServiceManager::UnloadService(std::initializer_list<const char*> names) {
  int res = 0;
  for (const auto &n : names) {
    std::unordered_map<std::string, Service*>::iterator it = services_.find(n);
    if (it != services_.end()) {
      delete it->second;
      services_.erase(n);
      res++;
      std::cout << "unload " << n << " success" << std::endl;
    }
  }
  return res;
}

ServiceManager::~ServiceManager() {
  std::cout << "~ServiceManager" << std::endl;
  for (auto &s : services_) {
	  delete s.second;
  }
  services_.clear();
}

void ServiceManager::run() {
  while (true) {
    // 打开命名管道进行通信
    std::ifstream pipe_in(pipe_name_); // 阻塞
    if (pipe_in.fail()) {
      std::cerr << "Failed to open pipe for reading." << std::endl;
      break;
    }
    std::string command;
    pipe_in >> command;  // 读取指令和模块名称

    std::string module_name;
    // 根据指令执行对应的操作
    if (command == "load") {
      while (pipe_in >> module_name) {
        LoadService({module_name.c_str()});
      }
    } else if (command == "reload") {
      while (pipe_in >> module_name)
        ReloadService({module_name.c_str()});
    } else if (command == "unload") {
      while (pipe_in >> module_name)
        UnloadService({module_name.c_str()});
    } else {
      std::cerr << "Invalid command: " << command << std::endl;
    }
    pipe_in.close();
  }
}

bool ServiceManager::listen(int argc, char* argv[]) {
  // 如果管道文件不存在就创建命名管道
  if (access(pipe_name_.c_str(), F_OK) == -1) {
    int res = mkfifo(pipe_name_.c_str(), 0777);
    if (res != 0)
    {
        fprintf(stderr, "Could not create fifo %s\n", pipe_name_.c_str());
        exit(EXIT_FAILURE);
    }
  }
  // not normally run
  if (argc >= 2 && (!strcmp(argv[1], "load") || !strcmp(argv[1], "reload") ||
                    !strcmp(argv[1], "unload"))) {
    // write to pipe
    std::ofstream pipe_out(pipe_name_);
    if (pipe_out.fail()) {
      std::cerr << "Failed to open pipe for writing." << std::endl;
      return false;
    }

    // 将指令和模块名称写入管道
    std::string command = argv[1];
    for (int i = 2; i < argc; ++i) {
      command += " ";
      command += argv[i];
    }
    pipe_out << command << std::endl;
    pipe_out.close();
    return false;
  }
  start();
  return true;
}