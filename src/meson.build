# 将 example-service.cc 编译为动态库
example_service = library('es',
    'example-service.cc',
    include_directories : [comm_inc],
    install_dir : libdir,
    install : true)

# 编译测试程序
executable('ldm-test',
    'main.cc',
    include_directories : [comm_inc],
    link_with: [ldm],
    install_rpath: libdir, # set ld_library_path
    install_dir : bindir,
    install : true)