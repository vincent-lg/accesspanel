# Copyright (c) 2016, LE GOFF Vincent
# Copyright (c) 2016, LE GOFF Vincent
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of ytranslate nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This file contains the ClientWindow class."""

import argparse
import os
import sys
import threading
import wx

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl

from accesspanel import AccessPanel

# Create the argument parser
parser = argparse.ArgumentParser()
parser.add_argument("server", help="the IRC server to connect to")
parser.add_argument("nick", help="the nick to be used")
parser.add_argument("channel", help="the channel's name")
parser.add_argument("-p", "--port", default=6667, type=int,
        help="the port to connect to")
parser.add_argument("-s", "--ssl", action="store_true",
        help="should the conneciton use SSL?")
parser.add_argument("-u", "--username", help="the username to be used")
parser.add_argument("-w", "--password", help="the password to be used")
args = parser.parse_args()

class IRCBot(irc.IRCClient):

    nickname = args.nick
    window = None
    nicks = {}

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        if self.window:
            self.window.send("~~~ Connected to the server. ~~~")

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        if self.window:
            self.window.send("~~~ Disconnected from the server. ~~~")

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        self.who()

    def who(self):
        "List the users in 'channel', usage: client.who('#testroom')"
        self.sendLine('who {}'.format(self.factory.channel))

    def irc_RPL_WHOREPLY(self, user, info):
        "Receive WHO reply from server"
        print(info)
        nick = info[2][:15]
        fullname = info[-1]
        self.nicks[nick] = fullname

    def receivedMOTD(self, motd):
        """A MOTD has been received."""
        msg = "MOTD:\n  " + "\n  ".join(motd)
        if self.window:
            self.window.send(msg)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        if self.window:
            self.window.send("~~~ Joined channel {}. ~~~".format(
                    self.factory.channel))

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        nick, _, host = user.partition('!')
        fullname = self.nicks.get(nick, nick)
        if self.window:
            self.window.send("<{}> {}".format(fullname, msg))

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        nick, _, host = user.partition('!')
        if self.window:
            self.window.send("{} {}".format(nick, msg))

class BotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """
    protocol = IRCBot

    def __init__(self, client, window):
        self.channel = args.channel
        self.client = client
        self.window = window

    def buildProtocol(self, addr):
        """Build the protocol."""
        built = protocol.ClientFactory.buildProtocol(self, addr)
        self.client.protocol = built
        built.window = self.window
        return built

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


class Connection(threading.Thread):

    """A thread to connect to the server."""

    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window
        self.protocol = None
        self.factory = BotFactory(self, window)
        self.hostname = args.server
        self.port = args.port
        if args.ssl:
            reactor.connectSSL(self.hostname, self.port, self.factory,
                    ssl.ClientContextFactory())
        else:
            reactor.connectTCP(self.hostname, self.port, self.factory)

    @property
    def nickname(self):
        """Return the nickname if defined in the protocol."""
        return self.protocol and self.protocol.nickname or ""

    def run(self):
        """Run the thread."""
        reactor.run(installSignalHandlers=0)

    def send(self, message):
        """Send the message to the IRC channel."""
        self.protocol.msg(self.factory.channel, message)


class ConversationsPanel(AccessPanel):

    """The access panel."""

    def __init__(self, window, connection):
        AccessPanel.__init__(self, window, history=True, lock_input=True)
        self.extensions["lock_input"].empty = True
        self.window = window
        self.connection = connection
        text = wx.TextCtrl(self, -1, "ok")

    def OnInput(self, message):
        """Send the text to the connection."""
        message = message.encode("utf-8", "replace")
        self.connection.send(message)
        self.Send("<{}> {}".format(self.connection.nickname, message))


class ConversationsWindow(wx.Frame):

    def __init__(self):
        super(ConversationsWindow, self).__init__(None)
        self.connection = Connection(self)

        # Window design
        self.panel = ConversationsPanel(self, self.connection)

        # Connection
        self.connection.start()

        # Event handler
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Display the window
        self.SetTitle("#cocomud-client")
        self.Maximize()
        self.Show()

    def OnClose(self, e):
        """The window is being closed."""
        reactor.stop()
        self.Destroy()

    def send(self, message):
        """Send to the panel."""
        self.panel.Send(message)

app = wx.App()
window = ConversationsWindow()
app.MainLoop()
