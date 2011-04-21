"""Augeas driver"""
__revision__ = '$Revision$'

import Bcfg2.Client.Tools
import os,augeas

"""
<Path type='augeas'
      name='/some/path'
      setting='setting'
      value='value'/>
"""

class Augeas(Bcfg2.Client.Tools.Tool):
    """Implement Augeas tool"""
    name = 'Augeas'
    __handles__ = [('Path', 'augeas')] 
    __req__ = {'Path': ['type', 'name', 'setting', 'value']}

    def __init__(self, logger, cfg, setup):
        Bcfg2.Client.Tools.Tool.__init__(self, logger, cfg, setup)
        self.augeas = augeas.augeas()
    
    def Verifyaugeas(self, entry, _):
        if entry.get('value') == None or \
                entry.get('setting') == None:
            self.logger.error('Entry %s not completely specified. '
                              'Try running bcfg2-repo-validate.' % (entry.get('name')))
        try:
            os.stat(entry.get('name'))
        except OSError, err:
            self.logger.debug("%s %s does not exist (%s)" %
                              (entry.tag, entry.get('name'), err))
            return False
        if len(self.augeas.match("/files/%s/%s" % (entry.get('name'), entry.get('setting')))) == 0:
            self.logger.debug('%s is not supported by any Augeas lens.' % (entry.get('name')))
            return False
        else:
            return True

    def Installaugeas(self, entry):
        self.augeas.set("/files/%s/%s" % (entry.get('name'), entry.get('setting')), entry.get('value'))

