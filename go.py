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

import datetime, time, os, ConfigParser as cfg

class SvnNotifier():

    def __init__(self, name, svn_root, svn_username, svn_password):
        self.name = name
        self.svn_root = svn_root
        self.svn_username = svn_username
        self.svn_password = svn_password
        self.last_revision = pysvn.Revision(pysvn.opt_revision_kind.number, 0)
        self.client = pysvn.Client()
        self.client.callback_get_login = self.credentials

    def notify(self, author, date, revision, message, paths):
        """Display the changed paths using libnotify"""
        title_string = 'New commit #%s to repository %s' % (revision, self.name)
        message_string = "[%s] %s: %s\n Paths: %s" % \
                        (date.strftime("%d.%m %H:%M"), author, message, paths)
        pynotify.Notification(title_string, message_string, "view-refresh").show()

    def credentials(self, realm, username, may_save):
        """Return the default login credentials"""
        return True, self.svn_username, self.svn_password, False

    def discover_changes(self):
        """
        Find out the changes occured since the last time this method is ran
        """
        log = self.client.log(
            self.svn_root,
            discover_changed_paths=True,
            revision_end=self.last_revision
            )
        log = log[:-1]   # Ignore last revision
        if len(log) > 0:
            self.last_revision = log[0].revision
            if len(log) > 3:
                pynotify.Notification("Older Commits for repository %s available" % self.name, None, "view-refresh").show()
                log = log[0:3]
            log.reverse()
            for entry in log:
                author = entry.get('author')
                rev = entry.revision.number
                message = entry.message
                date = datetime.datetime.fromtimestamp(entry.date)
                paths = []
                for change in entry.changed_paths:
                    if change.path not in paths:
                        paths.append(change.path)
                self.notify(author, date, rev, message, paths)


def main():
    path = os.path.dirname(__file__)
    config_file = os.path.join(path, 'svnnotify.cfg')
    repos = []
    try:
        parser = cfg.ConfigParser()
        parser.read(config_file)
        for section in parser.sections():
            server = parser.get(section, 'server')
            user = parser.get(section, 'user')
            passw = parser.get(section, 'pass')
            repos.append(SvnNotifier(section, server, user, passw))
            print 'Monitoring SVN repository %s: %s' % (section, server)
    except BaseException as e:
        print "Error while parsing file '%s':" % config_file
        print e
        exit()
    pynotify.init("SVN Monitor")
    print '- Press %s to quit -' % '^C'
    while True:
        for repo in repos:
            repo.discover_changes()
        time.sleep(60 * 10)  # Every 10 minutes

if __name__ == '__main__':
    main()
