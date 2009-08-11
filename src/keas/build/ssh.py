##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""SSH tools

$Id$
"""
import StringIO
import logging
import sys
from twisted.conch.ssh import transport, userauth, connection, channel
from twisted.conch.ssh.common import NS
from twisted.internet import defer, protocol, reactor
from keas.build import base

class Transport(transport.SSHClientTransport):
    user = None
    password = None
    cmd = None
    output = None

    def verifyHostKey(self, hostKey, fingerprint):
        base.logger.debug('host key fingerprint: %s' % fingerprint)
        return defer.succeed(1)

    def connectionSecure(self):
        conn = Connection()
        conn.cmd = self.cmd
        conn.output = self.output
        self.requestService(UserAuth(self.user, self.password, conn))


class UserAuth(userauth.SSHUserAuthClient):

    def __init__(self, user, password, instance):
        userauth.SSHUserAuthClient.__init__(self, user, instance)
        self.password = password

    def getPassword(self):
        return defer.succeed(self.password)

    def getPublicKey(self):
        return  # Empty implementation: always use password auth


class Connection(connection.SSHConnection):
    cmd = None

    def serviceStarted(self):
        channel = Channel(2**16, 2**15, self)
        channel.cmd = self.cmd
        channel.output = self.output
        self.openChannel(channel)


class Channel(channel.SSHChannel):
    name = 'session'    # must use this exact string
    cmd = None
    output = None

    def openFailed(self, reason):
        base.logger.error('"%s" failed: %s' % (self.cmd, reason))

    def channelOpen(self, data):
        self.welcome = data   # Might display/process welcome screen
        d = self.conn.sendRequest(self, 'exec', NS(self.cmd), wantReply=1)

    def dataReceived(self, data):
        self.output.write(data)

    def extReceived(self, dataType, data):
        self.output.write(data)

    def closed(self):
        self.loseConnection()
        reactor.stop()


def run(cmd, host, username, password):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(base.formatter)
    base.logger.addHandler(handler)

    output = StringIO.StringIO()
    def createTransport(*args, **kwargs):
        transport = Transport(*args, **kwargs)
        transport.user = username
        transport.password = password
        transport.cmd = cmd
        transport.output = output
        return transport
    protocol.ClientCreator(reactor, createTransport).connectTCP(host, 22)
    reactor.run()

    base.logger.removeHandler(handler)

    return output.getvalue()

if __name__ == '__main__':
    print run(*sys.argv[1:])
