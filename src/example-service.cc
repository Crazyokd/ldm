#include "ldm.h"

class ExampleService : public Service {
 public:
  bool start() {
    std::cout << "ExampleService start" << std::endl;
    return true;
  }
};

extern "C" Service* get_service() {
  return new ExampleService();
}