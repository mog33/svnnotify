#!/usr/bin/python
#
# script to notify the user for changes in a subversion repository.
#
# Depends on a configuration file with the following entries:
#
#   [server]
#   server=SVN_REPO_TO_MONITOR
#   user=YOUR_SVN_USERNAME
#   pass=YOUR_SVN_PASSWORD
#

try:
    import pysvn, pynotify
except:
    print "Error while loading external depencencies."
    print "Make sure 'pysvn' and 'pynotify' is installed."
    exit()

import datetime, time, ConfigParser as cfg

def read_config():
    """Read the configuration file containing server, username and password"""
    global svn_root, svn_username, svn_password

    config_file = 'svnnotify.cfg'
    config_header = 'server'

    try:
        parser = cfg.ConfigParser()
        parser.read(config_file)
        svn_root = parser.get(config_header, 'server')
        svn_username = parser.get(config_header, 'user')
        svn_password = parser.get(config_header, 'pass')
    except BaseException as e:
        print "Error while parsing file '%s':" % config_file
        print e
        exit()

def notify(paths, authors):
    """Display the changed paths using libnotify"""
    title_string = 'New commits to repository'
    path_string = ', '.join(paths)
    author_string = ', '.join(authors)
    message_string = path_string
    
    if pynotify.init("SVN Monitor"):
        n = pynotify.Notification(title_string, message_string, "emblem-shared")
        n.show()

def log_message(paths, authors, messages):
    """Print a log message containing the time, authors, paths, and messages"""
    now = datetime.datetime.now()
    now = now.strftime("%H:%M")
    path_string = ', '.join(paths)
    author_string = ', '.join(authors)
    message_string = ', '.join(messages)
    print "[%s] Paths: %s -- Authors: %s -- Messages: %s" % (now, path_string, author_string, message_string)
    

def credentials(realm, username, may_save):
    """Return the default login credentials"""
    return True, svn_username, svn_password, False

def discover_changes(last_revision=pysvn.Revision(pysvn.opt_revision_kind.number, 0)):
    """Find out the changes occured since the last time this method is ran"""
    if last_revision is None:
        last_revision=pysvn.Revision(pysvn.opt_revision_kind.number, 0)
    client = pysvn.Client()
    client.callback_get_login = credentials
    log = client.log(
        svn_root, 
        discover_changed_paths=True,
        revision_end=last_revision
        )
    if len(log) is 1:
        return last_revision, None, None, None
    authors = []
    paths = []
    messages = []
    for entry in log[:-1]:
        if entry.author not in authors:
            authors.append(entry.author)
        for change in entry.changed_paths:
            path = change.path #.split('/',2)[1]
            if path not in paths:
                paths.append(path)
        messages.append(entry.message)
    last_revision = log[0].revision
        
    return last_revision, authors, paths, messages

if __name__ == '__main__':
    read_config()
    print 'Monitoring SVN repository: %s' % svn_root
    print '- Press %s to quit -' % '^C'
    last_revision = None
    while True:
        last_revision, authors, paths, messages = discover_changes(last_revision)
        if paths is not None:
            log_message(paths, authors, messages)
            notify(paths, authors)
        time.sleep(30)
