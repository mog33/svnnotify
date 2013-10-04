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

import pynotify
import time
import os
import logging
from ConfigParser import ConfigParser

from appdirs import user_data_dir

from SvnRepoMonitor import SvnRepoMonitor


class SvnNotifier():
    def __init__(self, config_file, interval):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%d.%m.%Y %H:%M:%S",
            #filename= os.path.join(os.getcwd(), 'svnnotify.log')
        )
        self.interval = interval
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = self.get_config_file()
        self.repositories = self.create_repositories_from_svn_config()
        pynotify.init("SVN Monitor")
        logging.info("SvnNotifier created with configuration file %s monitoring %i repositories." % (
        self.config_file, len(self.repositories)))

    def run(self):
        while True:
            for repo in self.repositories:
                try:
                    repo.discover_changes()
                except Exception as e:
                    logging.error("Repo {0:s} not accessible\n{1:s}".format(repo.name, e))
            time.sleep(self.interval)

    def create_repositories_from_svn_config(self):
        logging.info("Reading configuration file %s" % self.config_file)
        config_parser = ConfigParser()
        config_parser.read(self.config_file)
        repositories = []
        for section in config_parser.sections():
            try:
                server = config_parser.get(section, 'server')
            except BaseException as e:
                logging.critical("Error while parsing config file %s\n%s" % (self.config_file, e))
                exit()
            if config_parser.has_option(section, 'user'):
                user = config_parser.get(section, 'user')
            else:
                user = None
            if config_parser.has_option(section, 'pass'):
                password = config_parser.get(section, 'pass')
            else:
                password = None
            repositories.append(SvnRepoMonitor(section, server, user, password, self.config_file))
            logging.info('Monitoring SVN repository %s (%s)' % (section, server))
        if repositories:
            return repositories
        else:
            logging.error("No sections in configuration file found. Aborting")
            exit()

    @staticmethod
    def get_config_file():
        cfg = os.path.join(os.getcwd(), "svnnotify.cfg")
        if os.path.isfile(cfg):
            return cfg
        cfg = os.path.join(user_data_dir("svnnotify"), "svnnotify.cfg")
        if os.path.isfile(cfg):
            return cfg
        logging.error("No configuration file found. Aborting")
        exit()


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Notifies about changes in SVN repositories")
    parser.add_argument("-c", "--config",
                        help="path to configuration file (default svnnotify.cfg in working directory or in %s)" % user_data_dir(
                            "svnnotify"))
    parser.add_argument("-v", "--version", help="shows version of svnnotify", action='version', version='%(prog)s 0.4')
    parser.add_argument("-i", "--interval", help="update interval in seconds (default 5 minutes)", type=int,
                        default=60 * 5)
    args = parser.parse_args()
    svn_notifier = SvnNotifier(args.config, args.interval)
    svn_notifier.run()
