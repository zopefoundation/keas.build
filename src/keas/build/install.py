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
"""Package Builder

$Id$
"""
__docformat__ = 'ReStructuredText'
import BeautifulSoup
import base64
import logging
import optparse
import pkg_resources
import re
import sys
import urllib2
from keas.build import base

logger = base.logger

class Installer(object):

    def __init__(self, options):
        self.options = options

    def getProjects(self):
        logger.debug('Package Index: ' + self.options.url)
        req = urllib2.Request(self.options.url)

        if self.options.username:
            base64string = base64.encodestring(
                '%s:%s' % (self.options.username, self.options.password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)

        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req).read())
        projects = [tag.get('href').replace('/', '')
                    for tag in soup('a')
                    if tag.parent.name == 'td' and tag.get('href') != '/']
        projects = sorted(projects)
        logger.debug('Found projects: %s' %' '.join(projects))
        return projects

    def getVariants(self, project):
        logger.debug('Package Index: ' + self.options.url)
        req = urllib2.Request(self.options.url + project)

        if self.options.username:
            base64string = base64.encodestring(
                '%s:%s' % (self.options.username, self.options.password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)

        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req).read())
        variants = []
        for tag in soup('a'):
            text = tag.contents[0]
            if not text.startswith(project):
                continue
            if len(text.split('-')) != 3:
                continue
            variant = text.split('-')[1]
            if variant in variants:
                continue
            variants.append(variant)
        variants = sorted(variants)
        logger.debug('Found variants: %s' %' '.join(variants))
        return variants

    def getVersions(self, project, variant):
        logger.debug('Package Index: ' + self.options.url)
        req = urllib2.Request(self.options.url + project)

        if self.options.username:
            base64string = base64.encodestring(
                '%s:%s' % (self.options.username, self.options.password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)

        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req).read())
        versions = []
        for tag in soup('a'):
            text = tag.contents[0]
            if not text.startswith(project+'-'+variant):
                continue
            version = text.split('-')[-1][:-4]
            if version in versions:
                continue
            versions.append(version)
        versions = sorted(
            versions, key=lambda x: pkg_resources.parse_version(x))
        logger.debug('Found versions: %s' %' '.join(versions))
        return versions

    def runCLI(self):
        # 1. Get the project to be installed.
        project = self.options.project
        if project is None:
            projects = self.getProjects()
            print 'Projects'
            for name in projects:
                print '  * ' + name
            project = base.getInput('Project', projects[0], False)
        # 2. Get the variant of the project.
        variant = self.options.variant
        if variant is None:
            variants = self.getVariants(project)
            print 'Variants'
            for name in variants:
                print '  * ' + name
            variant = base.getInput('Variant', variants[0], False)
        # 3. Get the version of the project.
        version = self.options.version
        if version is None:
            versions = self.getVersions(project, variant)
            if len(versions) == 0:
                print "Sorry, but there have not been any", project, variant, "releases yet."
                sys.exit(0)
            if self.options.latest:
                version = versions[-1]
            else:
                print 'Versions'
                for name in versions:
                    print '  * ' + name
                version = base.getInput('Version', versions[-1], False)
        # 4. Install the package
        base.do('%s -t 2 -%sc %s%s/%s-%s-%s.cfg' %(
            self.options.buildout,
            "vvvvv" if self.options.verbose else "",
            self.options.url,
            project,
            project, variant, version))

parser = optparse.OptionParser()
parser.add_option(
    "-u", "--url", action="store",
    dest="url", metavar="URL",
    help="The base URL at which the releases can be found.")

parser.add_option(
    "-p", "--project", action="store",
    dest="project", metavar="PROJECT",
    help="The name of the project to be installed.")

parser.add_option(
    "-V", "--variant", action="store",
    dest="variant", metavar="VARIANT",
    help="The variant of the project to be installed.")

parser.add_option(
    "-v", "--version", action="store",
    dest="version", metavar="VERSION",
    help="The version of the project to be installed.")

parser.add_option(
    "-l", "--latest", action="store_true",
    dest="latest", default=False,
    help="When specified, the latest version will be chosen.")

parser.add_option(
    "--username", action="store",
    dest="username", metavar="USER", default=None,
    help="The username needed to access the site.")

parser.add_option(
    "--password", action="store",
    dest="password", metavar="PASSWORD",
    help="The password needed to access the site.")

parser.add_option(
    "-b", "--buildout-path", action="store",
    dest="buildout", metavar="PATH", default="buildout",
    help="The path to the buildout executable.")

parser.add_option(
    "--quiet", action="store_true",
    dest="quiet", default=False,
    help="When specified, no messages are displayed.")

parser.add_option(
    "--verbose", action="store_true",
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

    installer = Installer(options)
    installer.runCLI()

    # Remove the handler again.
    logger.removeHandler(handler)

    # Exit cleanly.
    sys.exit(0)
