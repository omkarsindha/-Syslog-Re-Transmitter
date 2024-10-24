import socket
import time
import utils
import wx
import pcaplib
import Widgets


class Panel(wx.Panel):
    def __init__(self, parent, wxconfig):

        wx.Panel.__init__(self, parent)
        self.wxconfig = wxconfig
        self.parent = parent
        self.config = wx.Config()
        self.previewed_file = ""       # Stores the current previewed file's path so if user changes file it persists the data
        self.previewed_protocol = ""   # Stores the current previewed file's protocol
        self.destination_ips = {}
        self.destination_ports = {}
        self.timer = wx.Timer(self)
        self.animation_counter: int = 0

        self.main_vbox = wx.BoxSizer(wx.VERTICAL)
        main_box = wx.StaticBox(self)
        main_box.SetFont(wx.Font(wx.FontInfo(12).Bold()))
        main_box_sizer = wx.StaticBoxSizer(main_box)

        ip_label = wx.StaticText(self, label="Destination IP:")
        self.ip_cmb_bx = wx.ComboBox(self, size=(180, -1), style=wx.CB_READONLY)
        self.ip_cmb_bx.Bind(wx.EVT_COMBOBOX, self.update_list)
        self.ip_cmb_bx.Disable()

        port_label = wx.StaticText(self, label="Destination Port:")
        self.port_cmb_bx = wx.ComboBox(self, size=(150, -1), style=wx.CB_READONLY)
        self.port_cmb_bx.Bind(wx.EVT_COMBOBOX, self.update_list)
        self.port_cmb_bx.Disable()

        file_box_sizer = wx.BoxSizer()
        self.file_label = wx.StaticText(self, label="Source File:")
        self.file_name = wx.TextCtrl(self, style=wx.TE_READONLY, size=(400, -1),
                                     value=self.config.Read('/path', defaultVal=""))
        self.choose_file = wx.Button(self, label="Choose File")
        self.choose_file.Bind(wx.EVT_BUTTON, self.on_choose)

        choices = ['UDP', 'TCP']
        self.protocol_cmb_bx = wx.ComboBox(self, choices=choices, style=wx.CB_READONLY)
        self.protocol_cmb_bx.SetSelection(0)

        file_box_sizer.Add(self.file_label, 0, wx.EXPAND | wx.ALL, 5)
        file_box_sizer.Add(self.file_name, 0, wx.EXPAND | wx.ALL, 5)
        file_box_sizer.Add(self.choose_file, 0, wx.EXPAND | wx.ALL, 5)
        file_box_sizer.Add(self.protocol_cmb_bx, 0, wx.EXPAND | wx.ALL, 5)

        self.preview = wx.Button(self, label="Preview")
        self.preview.Bind(wx.EVT_BUTTON, self.on_preview)



        self.forward = wx.Button(self, label="Forward")
        # self.forward.Bind(wx.EVT_BUTTON, self.on_start)
        self.forward.Disable()

        grid = wx.GridBagSizer(4, 4)

        grid.Add(file_box_sizer, pos=(0, 0), span=(1,7), flag=wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add((0, 10), pos=(0, 7), flag=wx.LEFT | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=20)
        grid.Add(self.preview, pos=(0, 8), flag=wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(ip_label, pos=(1, 0), flag=wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(self.ip_cmb_bx, pos=(1, 1), flag=wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add((10, 10), pos=(1, 2))
        grid.Add(port_label, pos=(1, 3), flag=wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(self.port_cmb_bx, pos=(1, 4), flag=wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        grid.Add(self.forward, pos=(1, 8), flag=wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                 border=10)
        main_box_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 5)

        # List Control
        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.list_ctrl.InsertColumn(0, 'Index', width=50)
        self.list_ctrl.InsertColumn(1, 'Source', width=100)
        self.list_ctrl.InsertColumn(2, 'Destination', width=100)
        self.list_ctrl.InsertColumn(3, 'Length', width=50)
        self.list_ctrl.InsertColumn(4, 'Info',width=800)

        self.main_vbox.Add(main_box_sizer, flag=wx.RIGHT | wx.ALIGN_CENTER)
        self.main_vbox.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.SetSizer(self.main_vbox)

    def on_preview(self, event):
        path = self.file_name.GetValue()
        protocol = self.protocol_cmb_bx.GetStringSelection()

        self.previewed_file = path
        self.previewed_protocol = protocol

        if path =="":
            self.error_prompt("File not selected")
            self.set_status_text("File not selected :(")
            return

        self.destination_ips = {}
        self.destination_ports = {}
        cap = pcaplib.CapFile(filename=path)

        start_time = time.time()
        for packet in cap:
            if time.time() - start_time > 2:
                break

            if not isinstance(packet, pcaplib.Packet):
                continue

            if protocol == 'UDP':
                if not packet.udp_len:
                    continue
            elif protocol == 'TCP':
                if packet.udp_len:
                    continue

            if not packet.dst:  # Sometimes the destination is none
                continue

            ip = socket.inet_ntoa(packet.dst)
            if ip not in self.destination_ips:
                self.destination_ips[ip] = [packet]
            else:
                self.destination_ips[ip].append(packet)

            port = packet.dst_port
            if port not in self.destination_ports:
                self.destination_ports[port] = [packet]
            else:
                self.destination_ports[port].append(packet)

        sorted_destination_ips = dict(sorted(self.destination_ips.items(), key=lambda item: len(item[1]), reverse=True))
        sorted_destination_ports = dict(sorted(self.destination_ports.items(), key=lambda item: len(item[1]), reverse=True))

        self.ip_cmb_bx.Set([f"{key} ({len(sorted_destination_ips[key])} Packets)" for key in sorted_destination_ips])
        self.ip_cmb_bx.SetSelection(0)
        self.port_cmb_bx.Set([f"{key} ({len(sorted_destination_ports[key])} Packets)" for key in sorted_destination_ports])
        self.port_cmb_bx.SetSelection(0)
        self.forward.Enable()
        self.ip_cmb_bx.Enable()
        self.port_cmb_bx.Enable()
        self.set_status_text("The list and packet numbers are just for getting a feel of the file, they might not include all the packets!!!")
        self.update_list()

    def update_list(self, event=None):
        """Updates the list according to the current destination Port and IP"""
        self.list_ctrl.DeleteAllItems()

        if self.destination_ips or self.destination_ports:   # Check if there were any scans or not
            ip_key = self.ip_cmb_bx.GetStringSelection().split(" ")[0]
            port_key = self.port_cmb_bx.GetStringSelection().split(" ")[0]
            packets = self.destination_ips[ip_key]
            for packet in packets:
                if str(packet.dst_port) == port_key:
                    self.add_to_list(packet)
                if self.list_ctrl.GetItemCount() > 200:
                    break

    def on_forward(self, event):
        path = self.file_name.GetValue()
        if path == "":
            self.error_prompt("File not selected")
            self.set_status_text("File not selected :(")
            return

        cap = pcaplib.CapFile(filename=path)
        for packet in cap:
            if not isinstance(packet, pcaplib.Packet):
                continue

            ip = socket.inet_ntoa(packet.dst)
            if ip not in self.destination_ips:
                self.destination_ips[ip] = [packet]
            else:
                self.destination_ips[ip].append(packet)

            port = packet.dst_port
            if port not in self.destination_ports:
                self.destination_ports[port] = [packet]
            else:
                self.destination_ports[port].append(packet)

    def add_to_list(self, packet):
        src = socket.inet_ntoa(packet.src)
        dst = socket.inet_ntoa(packet.dst)

        i = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), '')
        self.list_ctrl.SetItem(i, 0, str(i+1))
        self.list_ctrl.SetItem(i, 1, src)
        self.list_ctrl.SetItem(i, 2, dst)
        self.list_ctrl.SetItem(i, 3, str(packet.udp_len))
        self.list_ctrl.SetItem(i, 4, utils.to_string(packet.get_payload()))

    def on_choose(self, event):
       wildcard = "Packet Capture files (*.pcap;*.pcapng)|*.pcap;*.pcapng|All files (*.*)|*.*"
       dialog = wx.FileDialog(self, "Choose a file", "", "", wildcard, wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
       if dialog.ShowModal() == wx.ID_OK:
           self.file_name.Clear()
           self.file_name.SetValue(dialog.GetPath())
           self.config.Write("/path", dialog.GetPath())
       dialog.Destroy()



    def set_status_text(self, text):
        self.parent.SetStatusText(text)

    # def OnTimer(self, event):
    #     """Called periodically while the flooder threads are running."""
    #     self.animation_counter += 1
    #     self.parent.SetStatusText(f"Test in progress{'.' * (self.animation_counter % 10)}")

    def error_prompt(self, message):
        dlg = wx.MessageDialog(self, message, "Error", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()


if __name__ == '__main__':
    import Main

    Main.Main()
