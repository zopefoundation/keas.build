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
"""Build a release

$Id$
"""
__docformat__ = 'ReStructuredText'
import BeautifulSoup
import ConfigParser
import StringIO
import base64
import logging
import pkg_resources
import re
import sys
import urllib2
from keas.build import base, package

logger = base.logger

def findProjectVersions(project, config, options):
    if options.offline:
        logger.info('Offline: Skip looking for project versions.')
        return []
    url = config.get(base.BUILD_SECTION, 'buildout-server') + project + '/'
    logger.debug('Package Index: ' + url)
    req = urllib2.Request(url)

    username = config.get(base.BUILD_SECTION, 'buildout-server-username')
    password = config.get(base.BUILD_SECTION, 'buildout-server-password')
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    req.add_header("Authorization", "Basic %s" % base64string)

    try:
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req).read())
    except urllib2.HTTPError, err:
        logger.error("There was an error accessing %s: %s" % (url, err))
        return []
    versions = [tag.contents[0][len(project)+1:-4]
                for tag in soup('a')
                if re.match(project+'-[0-9]', tag.contents[0])]

    return sorted(versions, key=lambda x: pkg_resources.parse_version(x))


def build(configFile, options):
    # Read the configuration file.
    logger.info('Loading configuration file: ' + configFile)
    config = ConfigParser.RawConfigParser()
    config.read(configFile)

    # Create the project config parser
    logger.info('Creating Project Configuration')
    projectParser = ConfigParser.RawConfigParser()
    if config.has_option(base.BUILD_SECTION, 'template'):
        template = config.get(base.BUILD_SECTION, 'template')
        logger.info('Loading Project Configuration Template: ' + template)
        projectParser.read([template])
    if not projectParser.has_section('versions'):
        projectParser.add_section('versions')

    # Determine all versions of the important packages
    for pkg in config.get(base.BUILD_SECTION, 'packages').split():
        customPath = None
        if ':' in pkg:
            pkg, customPath = pkg.split(':')
        builder = package.PackageBuilder(pkg, options)
        version = builder.runCLI(configFile, True)
        projectParser.set('versions', pkg, version)

    # Stop if no buildout-server given
    try:
        config.get(base.BUILD_SECTION, 'buildout-server')
    except ConfigParser.NoOptionError:
        logger.info('No buildout-server, stopping')
        return

    # Write the new configuration file to disk
    projectName = config.get(base.BUILD_SECTION, 'name')
    defaultVersion = configVersion = config.get(base.BUILD_SECTION, 'version')
    projectVersions = findProjectVersions(projectName, config, options)
    if projectVersions:
        defaultVersion = projectVersions[-1]
    if options.nextVersion or configVersion == '+':
        defaultVersion = base.guessNextVersion(defaultVersion)
    projectVersion = base.getInput(
        'Project Version', defaultVersion, options.useDefaults)

    projectConfigFilename = '%s-%s.cfg' %(projectName, projectVersion)
    logger.info('Writing project configuration file: ' + projectConfigFilename)
    projectParser.write(open(projectConfigFilename, 'w'))

    # Upload the release file
    if not options.offline and not options.noUpload:
        base.uploadFile(
            projectConfigFilename,
            config.get(base.BUILD_SECTION, 'buildout-server')+'/'+projectName,
            config.get(base.BUILD_SECTION, 'buildout-server-username'),
            config.get(base.BUILD_SECTION, 'buildout-server-password'),
            options.offline)

    # Create deployment configurations
    for section in config.sections():
        if section == base.BUILD_SECTION:
            continue
        logger.info('Building deployment configuration: ' + section)
        logger.info('Loading deploy template file: ' +
                    config.get(section, 'template'))
        template = file(config.get(section, 'template'), 'r').read()
        vars = dict([(name, value) for name, value in config.items(section)
                     if name != 'template'])
        vars['project-name'] = projectName
        vars['project-version'] = projectVersion
        vars['instance-name'] = section
        deployConfigText = template %vars
        deployConfigFilename = '%s-%s-%s.cfg' %(
            config.get(base.BUILD_SECTION, 'name'), section, projectVersion)
        deployConfig = ConfigParser.RawConfigParser()
        deployConfig.readfp(StringIO.StringIO(deployConfigText))
        deployConfig.set('buildout', 'extends', projectConfigFilename)
        logger.info('Writing deployment file: ' + deployConfigFilename)
        deployConfig.write(open(deployConfigFilename, 'w'))

        # Upload the deployment file
        if not options.offline and not options.noUpload:
            base.uploadFile(
                deployConfigFilename,
                config.get(
                    base.BUILD_SECTION, 'buildout-server')+'/'+projectName,
                config.get(base.BUILD_SECTION, 'buildout-server-username'),
                config.get(base.BUILD_SECTION, 'buildout-server-password'),
                options.offline)


def main(args=None):
    # Make sure we get the arguments.
    if args is None:
        args = sys.argv[1:]
    if not args:
        args = ['-h']

    # Set up logger handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(base.formatter)
    logger.addHandler(handler)

    # Parse arguments
    options, args = base.parser.parse_args(args)

    logger.setLevel(logging.INFO)
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    if options.quiet:
        logger.setLevel(logging.FATAL)

    build(options.configFile, options)

    # Remove the handler again.
    logger.removeHandler(handler)

    # Exit cleanly.
    sys.exit(0)
