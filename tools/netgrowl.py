#!/usr/bin/env python

# URL for this script: http://the.taoofmac.com/space/Projects/netgrowl.py
"""Growl 0.6 Network Protocol Client for Python"""
__version__ = "0.6" # will always match Growl version
__author__ = "Rui Carmo (http://the.taoofmac.com)"
__copyright__ = "(C) 2004 Rui Carmo. Code under BSD License."
__contributors__ = "Ingmar J Stein (Growl Team)"

import sys
import optparse
import struct
import md5
from socket import AF_INET, SOCK_DGRAM, socket

GROWL_UDP_PORT=9887
GROWL_PROTOCOL_VERSION=1
GROWL_TYPE_REGISTRATION=0
GROWL_TYPE_NOTIFICATION=1

class GrowlRegistrationPacket:
    """Builds a Growl Network Registration packet.
       Defaults to emulating the command-line growlnotify utility."""

    def __init__(self, application="growlnotify", password = None ):
        self.notifications = []
        self.defaults = [] # array of indexes into notifications
        self.application = application.encode("utf-8")
        self.password = password
    #   end def

    def addNotification(self, notification="Command-Line Growl Notification", enabled=True):
        """Adds a notification type and sets whether it is enabled on the GUI"""
        self.notifications.append(notification)
        if enabled:
            self.defaults.append(len(self.notifications)-1)
    #   end def

    def payload(self):
        """Returns the packet payload."""
        self.data = struct.pack( "!BBH",
                                 GROWL_PROTOCOL_VERSION,
                                 GROWL_TYPE_REGISTRATION,
                                 len(self.application) )
        self.data += struct.pack( "BB",
                                  len(self.notifications),
                                  len(self.defaults) )
        self.data += self.application
        for notification in self.notifications:
            encoded = notification.encode("utf-8")
            self.data += struct.pack("!H", len(encoded))
            self.data += encoded
        for default in self.defaults:
            self.data += struct.pack("B", default)
        self.checksum = md5.new()
        self.checksum.update(self.data)
        if self.password:
            self.checksum.update(self.password)
        self.data += self.checksum.digest()
        return self.data
    #   end def
  # end class

class GrowlNotificationPacket:
    """Builds a Growl Network Notification packet.
       Defaults to emulating the command-line growlnotify utility."""

    def __init__(self, application="growlnotify",
                 notification="Command-Line Growl Notification", title="Title",
                 description="Description", priority = 0, sticky = False, password = None ):
        self.application  = application.encode("utf-8")
        self.notification = notification.encode("utf-8")
        self.title        = title.encode("utf-8")
        self.description  = description.encode("utf-8")
        flags = (priority & 0x07) * 2
        if priority < 0:
            flags |= 0x08
        if sticky:
            flags = flags | 0x0001
        self.data = struct.pack( "!BBHHHHH",
                                 GROWL_PROTOCOL_VERSION,
                                 GROWL_TYPE_NOTIFICATION,
                                 flags,
                                 len(self.notification),
                                 len(self.title),
                                 len(self.description),
                                 len(self.application) )
        self.data += self.notification
        self.data += self.title
        self.data += self.description
        self.data += self.application
        self.checksum = md5.new()
        self.checksum.update(self.data)
        if password:
            self.checksum.update(password)
        self.data += self.checksum.digest()
    # end def

    def payload(self):
        """Returns the packet payload."""
        return self.data
    # end def
  # end class

def unit_test():
    print "Starting Unit Test"
    print " - please make sure Growl is listening for network notifications"
    #addr = ("localhost", GROWL_UDP_PORT)
    addr = ("192.168.0.192", GROWL_UDP_PORT)
    s = socket(AF_INET,SOCK_DGRAM)
    print "Assembling registration packet like growlnotify's (no password)"
    p = GrowlRegistrationPacket(password='hello')
    p.addNotification()
    print "Sending registration packet"
    s.sendto(p.payload(), addr)

    print "Assembling standard notification packet"
    p = GrowlNotificationPacket(password='hello')
    print "Sending standard notification packet"
    s.sendto(p.payload(), addr)

    print "Assembling priority -2 (Very Low) notification packet"
    p = GrowlNotificationPacket(priority=-2, password='hello')
    print "Sending priority -2 notification packet"
    s.sendto(p.payload(), addr)

    print "Assembling priority 2 (Very High) sticky notification packet"
    p = GrowlNotificationPacket(priority=2,sticky=True,password='hello')
    print "Sending priority 2 (Very High) sticky notification packet"
    s.sendto(p.payload(), addr)
    s.close()
    print "Done."

if __name__ == '__main__':
    parser = optparse.OptionParser(usage="%prog [OPTION]...",
                                   version="%prog1.0")
    parser.add_option('-n', '--name', dest='name',
                      help='Set the name of the application that sends the \
                      notification [Default: growlnotify]')
    parser.add_option('-s', '--sticky', dest='sticky',
                      help='Make the notification sticky')
    parser.add_option('-m', '--message', dest='message',
                      help='Sets the message to be used instead of using stdin')
    parser.add_option('-p', '--priority', dest='priority',
                       help='Specify an int or named key (default is 0)')
    parser.add_option('-H', '--host', dest='host', default='localhost',
                       help='Specify a hostname to which to send a remote \
                       notification.')
    parser.add_option('-P', '--password', dest='password', default="WRONG_PASSWORD",
                      help = 'Password used for remote notifications.')
    parser.add_option('', '--port',  dest='port', default=GROWL_UDP_PORT,
                      help = 'Port number for UDP notifications.')
    parser.add_option('-q', '--quiet', dest='quiet', default=False,
                      action="store_true", help="don't print debug info")

    options, args = parser.parse_args()

    assert options.password != 'WRONG_PASSWORD'

    if not args and not options:
        unit_test()
    else:
        addr = (options.host, options.port)
        s = socket(AF_INET, SOCK_DGRAM)
        if not options.quiet:
            print "Assembling standard notification packet"
        p = GrowlNotificationPacket(title=options.name,
                                    description=options.message,
                                    password=options.password)
        if not options.quiet:
            print "Sending standard notification packet"
        s.sendto(p.payload(), addr)
        s.close()

