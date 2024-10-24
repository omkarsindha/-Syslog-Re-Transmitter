import pcaplib
import wx
import utils
import socket
import time


class ForwardDialog(wx.Dialog):
    def __init__(self, parent, packet: pcaplib.Packet):
        super().__init__(parent, title="Forward Packet", size=(250, 200))
        self.parent = parent
        self.parent = parent
        self.packet = packet
        panel = wx.Panel(self)
        grid = wx.GridBagSizer()

        ip_label = wx.StaticText(panel, label="IP Address:")
        self.ip_entry = wx.TextCtrl(panel, value= self.parent.wxconfig.Read('/forwardIP', defaultVal=""))

        port_label = wx.StaticText(panel, label="Port:")
        self.port_entry = wx.TextCtrl(panel, value= self.parent.wxconfig.Read('/forwardPort', defaultVal=""))

        send_button = wx.Button(panel, label="Send")
        cancel_button = wx.Button(panel, label="Cancel")
        send_button.Bind(wx.EVT_BUTTON, self.on_send)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        self.prompt = wx.StaticText(panel, label="")
        grid.Add((-1, 5), pos=(0, 0))
        grid.Add(self.prompt, pos=(1, 0), span=(1, 2), flag= wx.LEFT | wx.ALIGN_CENTER_VERTICAL ,
                 border=27)
        grid.Add(ip_label, pos=(2, 0), flag=wx.TOP | wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(self.ip_entry, pos=(2, 1), flag=wx.TOP | wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(port_label, pos=(3, 0), flag=wx.TOP | wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(self.port_entry, pos=(3, 1), flag=wx.TOP | wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(send_button, pos=(4, 0), flag=wx.TOP | wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(cancel_button, pos=(4, 1), flag=wx.TOP | wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        panel.SetSizer(grid)

    def on_send(self, event):
        ip_address = self.ip_entry.GetValue()
        port = self.port_entry.GetValue()
        if not utils.is_valid_ip(ip_address):
            self.prompt.SetLabel("IP Address not valid")
            self.prompt.SetForegroundColour(wx.RED)
            return
        if not utils.is_valid_port(port):
            self.prompt.SetLabel("Port is not valid")
            self.prompt.SetForegroundColour(wx.RED)
            return
        self.parent.wxconfig.Write("/forwardIP", ip_address)
        self.parent.wxconfig.Write("/forwardPort", port)

        print(f"Sending to IP: {ip_address}:{port}")
        data = self.packet.get_payload()
        print(data)
        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # try:
        #     sock.sendto(data, (ip_address, port))
        #     time.sleep(1)
        #     print(f"Message sent to {ip_address}:{port}")
        # except Exception as e:
        #     print(f"Error sending message: {e}")
        # finally:
        #     sock.close()
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)


