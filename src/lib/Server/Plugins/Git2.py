"""The Git2 plugin provides a revision interface for Bcfg2 repos using git."""

import os
import dulwich
import Bcfg2.Server.Plugin

def createpath(path):
	if (os.path.exists(path) or path == '' ):
		return
	if (os.path.exists(os.path.dirname(path)) or os.path.dirname(path) == ''
):
		os.mkdir(path)
		return
	else:
		createpath(os.path.dirname(path))
		os.mkdir(path)
	return

class Git2(Bcfg2.Server.Plugin.Plugin,
          Bcfg2.Server.Plugin.Version):
    """Git2 is a version plugin for dealing with Bcfg2 repos."""
    name = 'Git2'
    __version__ = '0.1'
    __author__ = 'jsbillin@umich.edu'

    conflicts = ['Git']
    experimental = True
    __rmi__ = Bcfg2.Server.Plugin.Plugin.__rmi__ + ['Update']

    def __init__(self, core, datastore):
        Bcfg2.Server.Plugin.Plugin.__init__(self, core, datastore)
        Bcfg2.Server.Plugin.Version.__init__(self)
        self.core = core
        self.datastore = datastore
        self.logger.info("Git2 plugin starting initialization")
        try:
            self.client, self.host_path = dulwich.client.get_transport_and_path(self.datastore)
            self.repo = dulwich.repo.Repo(self.host_path)
            self.logger.info("Git2 plugin initialzed using repository at: %s" % self.host_path)
        except Exception, err:
            self.logger.error("Failed to read git repository; disabling git support: %s" % str(err))
            raise Bcfg2.Server.Plugin.PluginInitError
        
        # path to git directory for bcfg2 repo
        git_dir = "%s/.git" % datastore

        # Read revision from bcfg2 repo
        if os.path.isdir(git_dir):
            self.revision = self.get_revision()
        else:
            self.logger.error("%s is not a directory" % git_dir)
            raise Bcfg2.Server.Plugin.PluginInitError

        self.logger.debug("Initialized git plugin with git directory %s" % git_dir)

    def get_revision(self):
        """Read git revision information for the Bcfg2 repository."""
        try:
            revision = self.repo.head()
        except:
            self.logger.error("Failed to read git repository; disabling git support")
            raise Bcfg2.Server.Plugin.PluginInitError
        return revision

    def Update(self):
        '''Git2.Update() => True|False\nUpdate git working copy\n'''
        try:
            old_revision = self.revision
            self.logger.info("Git2: current revision: %s" % self.revision)
            remote_refs = self.client.fetch(self.host_path, self.repo,
                                       determine_wants=self.repo.object_store.determine_wants_all)
            self.repo["HEAD"] = remote_refs["HEAD"]
            revision = self.repo.head()
            if old_revision == revision:
            	self.logger.info("Git2: repository is current")
                return True
            else:
            	self.logger.info("Git2: revision: %s" % revision)
            tree_id = self.repo["HEAD"].tree
            for entry in self.repo.object_store.iter_tree_contents(tree_id):
                file_path = os.path.join(self.datastore,entry[0])
                createpath(os.path.dirname(file_path))
                if (entry[1] == 0120000):
                    os.symlink(file_path, entry[0])
                else:
                    file = open(file_path, 'wb')
                    file.write(repo.get_object(entry[2]).as_raw_string())
                    os.chmod(file_path, entry[1])
        except Exception, err:
            # try to be smart about the error we got back
            details = None
            # Need to define some tests for failure
            if details is None:
                self.logger.error("Git2: Failed to update server repository",
                                  exc_info=1)
            else:
                self.logger.error("Git2: Failed to update server repository: %s" %
                                  details)
            return False

        self.logger.info("Updated %s from revision %s to %s" % (self.datastore, old_revision, revision))
        self.revision = revision
        return True
