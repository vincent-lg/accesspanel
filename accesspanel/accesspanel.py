# Copyright (c) 2015, LE GOFF Vincent
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

"""Module containing the AccessPanel class.

The AccessPanel is a child of wx.Panel.  It behaves like an ordinary
panel with a multi-line text field taking all available room.  This
output field can serve as input, as well.

"""

import wx

# Event definition
myEVT_MESSAGE = wx.NewEventType()
EVT_MESSAGE = wx.PyEventBinder(myEVT_MESSAGE, 1)

class MessageEvent(wx.PyCommandEvent):

    """Event when a message is received."""

    def __init__(self, etype, eid, value=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Return the event's value."""
        return self._value


class AccessPanel(wx.Panel):

    def __init__(self, parent):
        super(AccessPanel, self).__init__(parent)
        self.editing_pos = 0

        # Window design
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # Output field
        output = wx.TextCtrl(self, size=(600, 400), style=wx.TE_MULTILINE)
        self.output = output

        # Add the output field in the sizer
        sizer.Add(output, proportion=8)

        # Event handler
        self.Bind(EVT_MESSAGE, self.OnMessage)
        output.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    @property
    def input(self):
        """Return the text being edited.

        This text should be between the editing position (editing_pos)
        and the end of the output field.

        """
        return self.output.GetRange(
                self.editing_pos, self.output.GetLastPosition())

    def is_editing(self, beyond_one=False):
        """Return True if editing, False sinon.

        We consider the user is editing if the cursor is in the input area.

        The 'beyond_one' parameter can be set to True if we want to
        test whether the cursor is at least one character ahead in
        the input field.

        """
        pos = self.output.GetInsertionPoint()
        if beyond_one:
            pos -= 1

        return pos < self.editing_pos

    def OnInput(self, message):
        """A message has been sent by pressing RETURN.

        This method should be overridden in child classes.

        """
        pass

    def OnMessage(self, e):
        """A message is received and should be displayed in the output field.

        This method is directly called in answer to the EVT_MESSAGE.
        It displays the received text in the window, being careful to
        put the cursor where it was before, with the typed text in
        the input field.

        """
        message = e.GetValue()

        # Normalize new lines
        message = message.replace("\r", "\n")
        message = message.replace("\n\n", "\n")
        message = message.replace("\n", "\r\n")
        if not message.endswith("\n"):
            message += "\r\n"

        pos = self.output.GetInsertionPoint()

        # Get the text before the editing line
        output = self.output.GetRange(0, self.editing_pos)
        input = self.input

        # Clears the output field and pastes the text back in
        self.output.SetValue(output)
        self.output.AppendText(message)
        # If the cursor is beyond the editing position
        if pos >= self.editing_pos:
            pos += len(message)

        # We have added some text, the editing position should be
        # at the end of the text
        self.editing_pos = self.output.GetLastPosition()
        self.output.AppendText(input)
        self.output.SetInsertionPoint(pos)

    def send(self, message):
        """Create an event to send the message to the window."""
        evt = MessageEvent(myEVT_MESSAGE, -1, message)
        wx.PostEvent(self, evt)

    def OnKeyDown(self, e):
        """A key is pressed in the output field."""
        skip = True
        pos = self.output.GetInsertionPoint()
        input = self.input
        modifiers = e.GetModifiers()
        key = e.GetUnicodeKey()
        if not key:
            key = e.GetKeyCode()

        # If the user has pressed RETURN
        if key == wx.WXK_RETURN and modifiers == 0:
            self.output.Remove(
                    self.editing_pos, self.output.GetLastPosition())
            self.editing_pos = self.output.GetLastPosition()
            self.OnInput(input)
            skip = False

        # If we press a letter before the input area, move it back there
        if pos < self.editing_pos and modifiers == 0:
            if 0 < key < 256:
                self.output.SetInsertionPoint(self.output.GetLastPosition())
                pos = self.output.GetInsertionPoint()

        # If we press backspace out of the input area
        if key == wx.WXK_BACK and modifiers == 0 and self.is_editing(True):
            skip = False

        if skip:
            e.Skip()
