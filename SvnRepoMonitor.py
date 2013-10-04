import pynotify
import datetime, logging
from pysvn import Client, Revision, opt_revision_kind
from ConfigParser import ConfigParser


class SvnRepoMonitor():

    def __init__(self, name, svn_root, svn_username, svn_password, config_file):
        self.name = name
        self.svn_root = svn_root
        self.svn_username = svn_username
        self.svn_password = svn_password
        self.client = Client()
        self.client.callback_get_login = self._credentials
        self.parser = ConfigParser()
        self.config_file = config_file

    def _notify(self, author, date, revision, message, paths):
        """Display the changed paths using libnotify"""
        title_string = 'New commit #%s in repository %s' % (revision, self.name)
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
        logging.debug("Open pynotify.Notification: %s | %s" % (title_string, message_string))
        pynotify.Notification(title_string, message_string, "view-refresh").show()

    def _credentials(self, realm, username, may_save):
        """Return the default login credentials"""
        return True, self.svn_username, self.svn_password, False

    def discover_changes(self):
        """
        Find out the changes occured since the last time this method is ran
        """
        logging.debug("Discover Changes in %s" % self.name)
        self.parser.read(self.config_file)
        if self.parser.has_option(self.name, "last_revision"):
            last_revision = self.parser.get(self.name, "last_revision")
        else:
            last_revision = 0
        log = self.client.log(
            self.svn_root,
            discover_changed_paths=True,
            revision_end=Revision(opt_revision_kind.number, last_revision)
            )
        log = log[:-1]   # Ignore last revision
        if len(log) > 0:
            logging.info("%s new commits in repository %s" % (len(log), self.name))
            # update last revision in config file
            last_revision = log[0].revision.number
            self.parser.set(self.name, "last_revision", last_revision)
            self.parser.write(open(self.config_file, 'w'))
            log.reverse()
            if len(log)>5: # Show only most recent commits
                pynotify.Notification("Even more commits in repository %s" % self.name, "There are %s more new commits in the repository" % (len(log)-5), "view-refresh").show()
                log = log [-5:]
            for entry in log:
                author = entry.get('author')
                rev = entry.revision.number
                message = entry.message
                date = datetime.datetime.fromtimestamp(entry.date)
                paths = []
                for change in entry.changed_paths:
                    paths.append(change.path)
                self._notify(author, date, rev, message, paths)
        else:
            logging.debug("No new commits in repository %s" % self.name)
 