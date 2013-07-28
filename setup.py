from distutils.core import setup
setup(name='svnnotify',
      version='0.1',
      author='Markus Graube',
      author_email='markus.graube@tu-dresden.de',
      description='Notify about changes in svn repositories',
      requires=['appdirs','pysvn','pynotify'],
      py_modules=['svnnotify']
      )
