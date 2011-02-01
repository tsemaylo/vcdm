import sys

from zope.interface import implements

from twisted.python import log
from twisted.internet import reactor
from twisted.web import server, resource, guard
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import FilePasswordDB, InMemoryUsernamePasswordDatabaseDontUse 

import vcdm
from vcdm.server.cdmi import RootCDMIResource

class SimpleRealm(object):
    """
    A realm which gives out L{RootResource} instances for authenticated users.
    """
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if resource.IResource in interfaces:
            return resource.IResource, RootCDMIResource(), lambda: None
        raise NotImplementedError()
    
def main():
    log.startLogging(sys.stdout)
    
    # Start datastore
    ds = vcdm.datastore_backends[vcdm.config.get('general', 'ds.backend')]
    ds.init()
    
    # for now just a small list of 
    checkers = [FilePasswordDB('users.db')]
    
    wrapper = guard.HTTPAuthSessionWrapper(
        Portal(SimpleRealm(), checkers),
        [guard.DigestCredentialFactory('md5', 'localhost:8080')])
    
    # unencrypted connection for testing/development
    reactor.listenTCP(8080, server.Site(resource=wrapper))
    
    # 1-way SSL for production
    from twisted.internet import ssl
    sslContext = ssl.DefaultOpenSSLContextFactory('server_credentials/key.pem','server_credentials/cert.pem')
    
    reactor.listenSSL(8081, server.Site(resource=wrapper), contextFactory = sslContext)
    
    # another connector without authorization requirements
    reactor.listenTCP(8082, server.Site(resource = RootCDMIResource()))
    
    # connector for providing quick metainfo
    from vcdm.server.meta.info import InfoResource
    reactor.listenTCP(8083, server.Site(resource = InfoResource()))
    
    reactor.run()

if __name__ == '__main__':
    main()