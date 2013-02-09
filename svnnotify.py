#!/usr/bin/python
#
# Script to notify the user for changes in a subversion repository.
#
# Depends on a configuration file with one or more of the following entries:
#
#   [ServerName]
#   server=SVN_REPO_TO_MONITOR
#   user=YOUR_SVN_USERNAME
#   pass=YOUR_SVN_PASSWORD
#

try:
    import pynotify
    from pysvn import Client, Revision, opt_revision_kind, ClientError
except ImportError:
    print("Error while loading external depencencies.")
    print("Make sure 'pysvn' and 'pynotify' are installed.")
    exit()

import datetime, time, os, ConfigParser as cfg, logging


class SvnNotifier():

    def __init__(self, name, svn_root, svn_username, svn_password, parser, config_file):
        self.name = name
        self.svn_root = svn_root
        self.svn_username = svn_username
        self.svn_password = svn_password
        self.client = Client()
        self.client.callback_get_login = self.credentials
        self.parser = parser
        self.config_file = config_file

    def notify(self, author, date, revision, message, paths):
        """Display the changed paths using libnotify"""
        title_string = 'New commit #%s to repository %s' % (revision, self.name)
        message_string = "<p>[%s] %s</p> <p><i>%s</i>" % \
                        (date.strftime("%d.%m %H:%M"), author, message)
        message_string += "<ul>"
        for p in paths[:5]:
            if len(p)>50:
                p = "...%s" % p[-50:]
            message_string += "<li>%s</li>" % p
        if len(paths)>6:
            message_string += "<li>...</li>"
        message_string += "</ul></p>"
        logging.debug("Open pynotify.Notification: %s | %s" % (title_string,message_string))
        pynotify.Notification(title_string, message_string, "view-refresh").show()

    def credentials(self, realm, username, may_save):
        """Return the default login credentials"""
        return True, self.svn_username, self.svn_password, False

    def discover_changes(self):
        """
        Find out the changes occured since the last time this method is ran
        """
        logging.debug("Discover Changes in %s" % self.name)
        try:
            self.parser.read(self.config_file)
            last_revision = self.parser.get(self.name, "last_revision")
        except cfg.NoOptionError:
            last_revision = 0
        log = self.client.log(
            self.svn_root,
            discover_changed_paths=True,
            revision_end=Revision(opt_revision_kind.number, last_revision)
            )
        log = log[:-1]   # Ignore last revision
        if len(log) > 0:
            logging.info("%s new commits for %s" % (len(log), self.name))
            # update last revision in config file
            last_revision = log[0].revision.number
            self.parser.set(self.name, "last_revision", last_revision)
            self.parser.write(open(self.config_file, 'w'))
            log.reverse()
            if len(log)>5: # Show only last 10 commits
                pynotify.Notification("Even more commits for repository %s" % self.name, "There are %s more new commits in the repository" % (len(log)-5), "view-refresh").show()
                log = log [-5:]
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
        else:
            logging.info("No new commits for %s" % self.name)


def main():
    path = os.path.dirname(__file__)
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s %(levelname)s: %(message)s",
        datefmt = "%d.%m.%Y %H:%M:%S",
        filename= os.path.join(path, 'svnnotify.log'))
    config_file = os.path.join(path, 'svnnotify.cfg')
    repos = []
    try:
        parser = cfg.ConfigParser()
        parser.read(config_file)
        for section in parser.sections():
            server = parser.get(section, 'server')
            if parser.has_option(section, 'user'):
                user = parser.get(section, 'user')
            else:
                user = None
            if parser.has_option(section, 'pass'):
                passw = parser.get(section, 'pass')
            else:
                passw = None
            repos.append(SvnNotifier(section, server, user, passw, parser, config_file))
            logging.info('Monitoring SVN repository %s (%s)' % (section, server))
    except BaseException as exception:
        logging.critical("Error while parsing file '%s':" % config_file)
        logging.critical(exception)
        exit()
    pynotify.init("SVN Monitor")

    while True:
        for repo in repos:
            try:
                repo.discover_changes()
            except ClientError as e:
                logging.error("Repo %s not accessible" % repo.name)
                logging.error(e)
        time.sleep(60 * 5)  # Every 5 minutes

if __name__ == '__main__':
    main()
