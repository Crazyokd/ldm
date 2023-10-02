project('ldm', ['c', 'cpp'])

add_project_arguments(
  '-xc++',
  language : 'c'
)
cc = meson.get_compiler('cpp')

prefix = run_command('sh', '-c', 'echo $PWD', check : true).stdout().strip() / 'install'
bindir = join_paths(prefix, get_option('bindir'))
libdir = join_paths(prefix, get_option('libdir'))

comm_inc = include_directories('''
    include
'''.split())


subdir('lib')
subdir('src')
