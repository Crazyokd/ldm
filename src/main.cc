#include "ldm.h"


int main(int argc, char* argv[]) {
  ServiceManager sm;
  if (!sm.listen(argc, argv)) {
    return -1;
  } else {
    std::cout << "ServiceManager start successfully" << std::endl;
  }
  // 模拟后台程序
  while (true) std::this_thread::sleep_for(std::chrono::milliseconds(1000));
  return 0;
}
