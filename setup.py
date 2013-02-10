from distutils.core import setup
setup(name='svnnotify',
      version='0.1',
      author='mog33',
      author_email='ctrl.alt.del@gmx.net',
      description='Notify about changes in svn repositories',
      requires='appdirs',
      py_modules=['svnnotify'],
      data_files=[('', ['svnnotify-sample.cfg', ]),]
      )
