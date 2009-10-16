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
"""Package Deployment

$Id$
"""

#
# WARNING
# this was never working completely
#
# Stephan says: it should be moved to use command-line SSH
# AdamG says: twisted was a pain on windows
#             keeping it around to have the idea what should be done
#

__docformat__ = 'ReStructuredText'
import ConfigParser
import logging
import optparse
import subprocess
import sys
from keas.build import base #, ssh

logger = base.logger

def doSSH(cmd, host, username, password):
    logger.info('%s:%s@%s # %s' %(username, password, host, cmd))
    # Since I am too stupid to understand twisted, we execute the ssh command
    # in a sub-process.
    line = sys.executable
    line += ' -c "import sys; sys.path = %r; ' %sys.path
    line += 'from keas.build import ssh; '
    line += 'print ssh.run(%r, %r, %r, %r)"' %(cmd, host, username, password)
    p = subprocess.Popen(
        line,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    if p.returncode != 0:
        logger.error(u'An error occurred while running command: %s' %cmd)
        error = p.stderr.read()
        logger.error('Error Output: \n' + error)
        sys.exit(p.returncode)
    error = p.stderr.read()
    if error:
        logger.error('Error Output: \n' + error)
    output = p.stdout.read()
    if output:
        logger.debug('Output: \n' + output)
    return output

class Deployment(object):

    def __init__(self, options):
        self.options = options

    def runCLI(self):
        # 1. Read the configuration file.
        logger.info('Loading configuration file: ' + self.options.configFile)
        config = ConfigParser.RawConfigParser()
        config.read(self.options.configFile)
        # 2. Deploy each component listed in the configuration
        for section in config.sections():
            logger.info('Deploying ' + section)
            for cmd in config.get(section, 'commands').strip().split('\n'):
                logger.debug('Run command: ' + cmd)
                result = doSSH(
                    cmd,
                    config.get(section, 'server'),
                    config.get(section, 'username'),
                    config.get(section, 'password'))
                logger.debug(result)

parser = optparse.OptionParser()
parser.add_option(
    "-c", "--config-file", action="store",
    dest="configFile", metavar="FILE",
    help="The file containing the deployment configuration.")

parser.add_option(
    "-q", "--quiet", action="store_true",
    dest="quiet", default=False,
    help="When specified, no messages are displayed.")

parser.add_option(
    "-v", "--verbose", action="store_true",
    dest="verbose", default=False,
    help="When specified, debug information is created.")

def main(args=None):
    # Make sure we get the arguments.
    if args is None:
        args = sys.argv[1:]
    if not args:
        args = ['-h']

    # Set up logger handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(base.formatter)
    logger.addHandler(handler)

    # Parse arguments
    options, args = parser.parse_args(args)

    logger.setLevel(logging.INFO)
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    if options.quiet:
        logger.setLevel(logging.FATAL)

    deployment = Deployment(options)
    deployment.runCLI()

    # Remove the handler again.
    logger.removeHandler(handler)

    # Exit cleanly.
    sys.exit(0)
