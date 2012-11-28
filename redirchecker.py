#!/bin/env python

########################################
# Copyright 2012 Michal Rysavy
# This program is distributed under the terms of the GNU General Public License
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
########################################

import urllib2
import socket
from argparse import ArgumentParser
from ConfigParser import SafeConfigParser

class RedirectChecker:
    class redirection:
        def __init__( self, source, target, code, server, message ):
            self.source = source;
            self.target = target;
            self.code = code;
            self.server = server;
            self.message = message;

    def __init__( self, url, expected_url, expected_code = 200 ):
        expected_code = int(expected_code);
        
        self.url = url;
        self.redirections = [];

        opener = urllib2.build_opener( RedirectHandler( self ), HTTPErrorHandler );

        self.successful = False;
        self.satisfied = False;

        try:
            response = opener.open( self.url );

            self.successful = True;
            self.finalurl = response.geturl();
            self.code = response.getcode();

            self.satisfied = ( self.finalurl == expected_url and self.code == expected_code );

        except socket.error, ( errno, string ):
            self.errno = errno;
            self.errstr = string;
        except urllib2.URLError, ( reason ):
            self.errno = None;
            self.errstr = str(reason);

    def getURL( self ):
        return self.url;

    def getFinalURL( self ):
        return self.finalurl;

    def getCode( self ):
        return self.code;

    def getRedirections( self ):
        return self.redirections;

    def getErrNo( self ):
        return self.errno;

    def getErrStr( self ):
        return self.errstr;

    def isSuccessful( self ):
        return self.successful;

    def isSatisfied( self ):
        return self.satisfied;

class RedirectHandler( urllib2.HTTPRedirectHandler ):
    def __init__( self, checker ):
        self.checker = checker;

    def redirect_request( self, req, fp, code, msg, headers, newurl ):
        redirection = RedirectChecker.redirection( req.get_full_url(), newurl, code, headers.getheader( 'Server' ), msg );
        self.checker.redirections.append( redirection );

        result = urllib2.HTTPRedirectHandler.redirect_request( self, req, fp, code, msg, headers, newurl );
        return result;

class HTTPErrorHandler ( urllib2.HTTPDefaultErrorHandler ):
    def http_error_default( self, req, fp, code, msg, hdrs ):
        return fp;

def parse_args():
    parser = ArgumentParser( description = 'Redirections Checker' );
    parser.add_argument( '-f', '--configfile', required = True, help = 'Configuration file' );

    return parser.parse_args();

def parse_cfg( cfgfile ):
    config = SafeConfigParser();
    config.read( cfgfile );
    return config;

args = parse_args();
config = parse_cfg( args.configfile );

for section_name in config.sections():
    url = config.get( section_name, 'url' );
    expected = config.get( section_name, 'expected' );
    code = config.get( section_name, 'code' ) if config.has_option( section_name, 'code' ) else 200;

    checker = RedirectChecker( url, expected, code );
    redirections = checker.getRedirections();

    print; print; print;
    print 'CHECKING: ' + url;

    if not checker.isSuccessful():
        print '..... UNSUCCESSFUL: ' + str( checker.getErrNo() ) + ' [' + checker.getErrStr() + ']';
        continue;

    if not checker.isSatisfied():
        print '..... UNSATISFIED: ' + checker.getFinalURL() + ' [' + str( checker.getCode() ) + ']';

    if checker.isSatisfied():
        print '..... OK: ' + str( checker.getFinalURL() ) + ' [' + str( checker.getCode() ) + ']';

    print;
    for redirection in redirections:
        print '..... REDIRECT [' + str( redirection.code ) + '] ' + redirection.source + ' ==> ' + redirection.target + ' [' + ( redirection.server if redirection.server else '' ) + ': ' + ( redirection.message if redirection.message else '' ) + ']' ;
