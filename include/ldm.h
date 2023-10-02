#ifndef LDM_H_
#define LDM_H_

#include <cstdarg>
#include <dlfcn.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

#include <initializer_list>
#include <unordered_map>
#include <vector>
#include <thread>
#include <fstream>
#include <iostream>
#include <atomic>


enum THREAD_STATE
{
	THREAD_STOPED,
	THREAD_RUNNING,
};

enum THREAD_ERROR
{
	THREAD_OK,
	THREAD_ALREADY_RUNNING,
	THREAD_FAIL,
};


class AbstractRunnable
{
private:
	THREAD_STATE state;
	bool should_stop;
	std::thread *t;

private:
	void ThreadMethod()
	{
		state = THREAD_RUNNING;
		try {
			run();
		}
		catch(std::exception &ex) {
			state = THREAD_STOPED;
			throw ex;
		}
		catch(...) {
			state = THREAD_STOPED;
			throw;
		}
		
		state = THREAD_STOPED;
	}
	
	virtual void run() = 0;

protected:
	bool check_stop() { return should_stop; }

public:
	AbstractRunnable()
	{
		state = THREAD_STOPED;
		should_stop = false;
		t = NULL;
	}
	
	virtual ~AbstractRunnable()
	{
		stop();
		if(t)
		{
			t->join();
			delete t;
		}
	}
	
	virtual THREAD_ERROR start()
	{
		if(state == THREAD_RUNNING)
			return THREAD_ALREADY_RUNNING;
	
		if(t) delete t;
		t = new std::thread(&AbstractRunnable::ThreadMethod, this);
		if(!t)
			return THREAD_FAIL;
	
		should_stop = false;
		return THREAD_OK;
	}
	
	virtual void stop()
	{
		if(t)
		{
			should_stop = true;
			t->join();
			delete t;
			t = NULL;
		}
		state = THREAD_STOPED;
	}

	std::thread* thread() { return t; }
	THREAD_STATE status() { return state; }
};


class Service {
 public:
  virtual ~Service() {
    if (handle_) {
      dlclose(handle_);
      handle_ = nullptr;
    }
  }
  // 启动服务
  virtual bool start() = 0;
 private:
  // 动态库句柄
  void *handle_;
};

class ServiceManager final : public AbstractRunnable {
 public:
  typedef Service* (*GetServiceFunc)();
  int LoadService(std::initializer_list<const char*> names);
  int ReloadService(std::initializer_list<const char*> names);
  int UnloadService(std::initializer_list<const char*> names);
  bool listen(int argc, char* argv[]);
  ~ServiceManager();
  ServiceManager(std::string pipe_name = "service_pipe")
    : pipe_name_(pipe_name) {}
 private:
  void run() override;
  std::unordered_map<std::string, Service*> services_;
  std::string pipe_name_;
};


#endif