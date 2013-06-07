"""VCS support."""

# TODO:
#   * git_write_index
#   * add svn support
#   * integrate properly with reports
missing = []

import errno
import os
import shutil
import sys

# python-dulwich git imports
try:
    import dulwich
    import dulwich.index
    from dulwich.errors import NotGitRepository
except ImportError:
    missing.append('git')
# subversion import
try:
    import pysvn
except ImportError:
    missing.append('svn')

import Bcfg2.Client.Tools


class VCS(Bcfg2.Client.Tools.Tool):
    """VCS support."""
    __handles__ = [('Path', 'vcs')]
    __req__ = {'Path': ['name',
                        'type',
                        'vcstype',
                        'sourceurl',
                        'revision']}

    def git_write_index(self, entry):
        """Write the git index"""
        pass

    def Verifygit(self, entry, _):
        """Verify git repositories"""
        try:
            repo = dulwich.repo.Repo(entry.get('name'))
        except NotGitRepository:
            self.logger.info("Repository %s does not exist" %
                             entry.get('name'))
            return False

        try:
            expected_rev = entry.get('revision')
            cur_rev = repo.head()
        except:
            return False

        try:
            client, path = dulwich.client.get_transport_and_path(entry.get('sourceurl'))
            remote_refs = client.fetch_pack(path, (lambda x: None), None, None, None)
            if expected_rev in remote_refs:
                expected_rev = remote_refs[expected_rev]
        except:
            pass

        if cur_rev != expected_rev:
            self.logger.info("At revision %s need to go to revision %s" %
                             (cur_rev.strip(), expected_rev.strip()))
            return False

        return True

    def Installgit(self, entry):
        """Checkout contents from a git repository"""
        destname = entry.get('name')
        if os.path.lexists(destname):
            # remove incorrect contents
            try:
                if os.path.isdir(destname):
                    shutil.rmtree(destname)
                else:
                    os.remove(destname)
            except OSError:
                self.logger.info('Failed to remove %s' %
                                 destname)
                return False

        dulwich.file.ensure_dir_exists(destname)
        destr = dulwich.repo.Repo.init(destname)
        cl, host_path = dulwich.client.get_transport_and_path(entry.get('sourceurl'))
        remote_refs = cl.fetch(host_path,
                               destr,
                               determine_wants=destr.object_store.determine_wants_all,
                               progress=sys.stdout.write)

        if entry.get('revision') in remote_refs:
            destr.refs['HEAD'] = remote_refs[entry.get('revision')]
        else:
            destr.refs['HEAD'] = entry.get('revision')

        dtree = destr['HEAD'].tree
        for fname, mode, sha in destr.object_store.iter_tree_contents(dtree):
            full_path = os.path.join(destname, fname)
            dulwich.file.ensure_dir_exists(os.path.dirname(full_path))

            if dulwich.objects.S_ISGITLINK(mode):
                src_path = destr[sha].as_raw_string()
                try:
                    os.symlink(src_path, full_path)
                except OSError:
                    e = sys.exc_info()[1]
                    if e.errno == errno.EEXIST:
                        os.unlink(full_path)
                        os.symlink(src_path, full_path)
                    else:
                        raise
            else:
                file = open(full_path, 'wb')
                file.write(destr[sha].as_raw_string())
                file.close()
                os.chmod(full_path, mode)

        return True
        # FIXME: figure out how to write the git index properly
        #iname = "%s/.git/index" % entry.get('name')
        #f = open(iname, 'w+')
        #entries = obj_store[sha].iteritems()
        #try:
        #    dulwich.index.write_index(f, entries)
        #finally:
        #    f.close()

    def Verifysvn(self, entry, _):
        """Verify svn repositories"""
        client = pysvn.Client()
        try:
            cur_rev = str(client.info(entry.get('name')).revision.number)
        except:
            self.logger.info("Repository %s does not exist" % entry.get('name'))
            return False

        if cur_rev != entry.get('revision'):
            self.logger.info("At revision %s need to go to revision %s" %
                             (cur_rev, entry.get('revision')))
            return False

        return True

    def Installsvn(self, entry):
        """Checkout contents from a svn repository"""
        # pylint: disable=E1101
        client = pysvn.Client()
        try:
            client.update(entry.get('name'), recurse=True)
        except pysvn.ClientError:
            self.logger.error("Failed to update repository", exc_info=1)
            return False
        return True
        # pylint: enable=E1101

    def VerifyPath(self, entry, _):
        vcs = entry.get('vcstype')
        if vcs in missing:
            self.logger.error("Missing %s python libraries. Cannot verify" %
                              vcs)
            return False
        ret = getattr(self, 'Verify%s' % vcs)
        return ret(entry, _)

    def InstallPath(self, entry):
        vcs = entry.get('vcstype')
        if vcs in missing:
            self.logger.error("Missing %s python libraries. "
                              "Unable to install" % vcs)
            return False
        ret = getattr(self, 'Install%s' % vcs)
        return ret(entry)
