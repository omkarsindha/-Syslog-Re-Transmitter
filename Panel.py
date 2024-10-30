import random
import socket
import time
import utils
import wx
import pcaplib
import Widgets
import Threads

class Panel(wx.Panel):
    def __init__(self, parent, wxconfig):
        wx.Panel.__init__(self, parent)
        self.wxconfig = wxconfig
        self.parent = parent
        self.destination_ips:dict[str,list] = {}
        self.destination_ports:dict[str,list] = {}
        self.re_transmit_thread: Threads.ReTransmitPacketsThread = None

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.animation_counter: int = 0

        self.main_vbox = wx.BoxSizer(wx.VERTICAL)
        main_box = wx.StaticBox(self)
        main_box.SetFont(wx.Font(wx.FontInfo(12).Bold()))
        main_box_sizer = wx.StaticBoxSizer(main_box)

        file_box_sizer = wx.BoxSizer()
        self.file_label = wx.StaticText(self, label="Source File:")
        self.file_name = wx.TextCtrl(self, style=wx.TE_READONLY, size=(400, -1))
        self.choose_file = wx.Button(self, label="Choose File")
        self.choose_file.Bind(wx.EVT_BUTTON, self.on_choose)

        file_box_sizer.Add(self.file_label, 0, wx.EXPAND | wx.ALL, 5)
        file_box_sizer.Add(self.file_name, 0, wx.EXPAND | wx.ALL, 5)
        file_box_sizer.Add(self.choose_file, 0, wx.EXPAND | wx.ALL, 5)

        self.progress_bar = Widgets.ProgressBarWidget(self)

        trg_ip_label = wx.StaticText(self, label="Target IP:")
        self.ip_cmb_bx = wx.ComboBox(self, size=(180, -1), style=wx.CB_READONLY)
        self.ip_cmb_bx.Bind(wx.EVT_COMBOBOX, self.update_list)

        trg_port_label = wx.StaticText(self, label="Target Port:")
        self.port_cmb_bx = wx.ComboBox(self, size=(150, -1), style=wx.CB_READONLY)
        self.port_cmb_bx.Bind(wx.EVT_COMBOBOX, self.update_list)

        self.protocol_cmb_bx = wx.ComboBox(self, choices=['UDP', 'TCP'], style=wx.CB_READONLY)
        self.protocol_cmb_bx.SetSelection(0)
        self.protocol_cmb_bx.Bind(wx.EVT_COMBOBOX, self.update_list)

        self.settings_box_sizer = wx.BoxSizer()
        self.settings_box_sizer.Add(trg_ip_label, 0, wx.EXPAND | wx.RIGHT, 5)
        self.settings_box_sizer.Add(self.ip_cmb_bx, 0, wx.EXPAND | wx.RIGHT, 15)
        self.settings_box_sizer.Add(trg_port_label, 0, wx.EXPAND | wx.RIGHT, 5)
        self.settings_box_sizer.Add(self.port_cmb_bx, 0, wx.EXPAND | wx.RIGHT, 15)
        self.settings_box_sizer.Add(self.protocol_cmb_bx, 0, wx.EXPAND | wx.LEFT, 5)
        for item in self.settings_box_sizer.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Disable()

        dst_ip_label = wx.StaticText(self, label="Destination IP:")
        self.dst_ip_input = wx.TextCtrl(self, value=self.wxconfig.Read('/forwardIP', defaultVal=""),
                                        size=(100, -1))

        dst_port_label = wx.StaticText(self, label="Destination Port:")
        self.dst_port_input = wx.TextCtrl(self, value=self.wxconfig.Read('/forwardPort', defaultVal=""),
                                      size=(50, -1))
        rate_label = wx.StaticText(self, label="Packets/Sec:")
        self.rate_input = wx.TextCtrl(self, value=self.wxconfig.Read('/forwardRate', defaultVal=""),
                                          size=(40, -1))
        pkt_ls_lbl = wx.StaticText(self, label="Packet Loss % :")
        self.loss_input = wx.TextCtrl(self, value=self.wxconfig.Read('/forwardLoss', defaultVal=""),
                                       size=(40, -1))
        self.frwd_box1 = wx.BoxSizer()
        self.frwd_box1.Add(dst_ip_label, 0, wx.EXPAND | wx.RIGHT, 5)
        self.frwd_box1.Add(self.dst_ip_input, 0, wx.EXPAND | wx.RIGHT, 15)
        self.frwd_box1.Add(dst_port_label, 0, wx.EXPAND | wx.RIGHT, 5)
        self.frwd_box1.Add(self.dst_port_input, 0, wx.EXPAND | wx.RIGHT, 15)
        self.frwd_box1.Add(rate_label, 0, wx.EXPAND | wx.RIGHT, 5)
        self.frwd_box1.Add(self.rate_input, 0, wx.EXPAND | wx.RIGHT, 15)
        self.frwd_box1.Add(pkt_ls_lbl, 0, wx.EXPAND | wx.RIGHT, 5)
        self.frwd_box1.Add(self.loss_input, 0, wx.EXPAND | wx.RIGHT, 15)
        for item in self.frwd_box1.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Disable()

        source_label = wx.StaticText(self, label="Syslog Traffic Controller Tagging")
        self.source_ck_bx = wx.CheckBox(self)
        chk_bx_val = self.wxconfig.Read('/trafficController', defaultVal="")
        if chk_bx_val == "True":
            self.source_ck_bx.SetValue(True)

        index_label = wx.StaticText(self, label="Start Index:")
        self.index_input = wx.TextCtrl(self, value=self.wxconfig.Read('/forwardIndex', defaultVal=""), size=(60, -1))
        self.forward = wx.Button(self, label="Play Out")
        self.forward.Bind(wx.EVT_BUTTON, self.on_forward)
        self.pause = wx.Button(self, label="Pause")
        self.pause.Bind(wx.EVT_BUTTON, self.on_pause)
        self.stop = wx.Button(self, label="Stop")
        self.stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.frwd_box2 = wx.BoxSizer()
        self.frwd_box2.Add(source_label, 0, wx.EXPAND | wx.TOP | wx.RIGHT, 5)
        self.frwd_box2.Add(self.source_ck_bx, 0, wx.EXPAND | wx.RIGHT, 10)
        self.frwd_box2.Add(index_label, 0, wx.EXPAND | wx.TOP | wx.RIGHT, 5)
        self.frwd_box2.Add(self.index_input, 0, wx.EXPAND | wx.RIGHT, 30)
        self.frwd_box2.Add(self.forward, 0, wx.EXPAND | wx.RIGHT, 10)
        self.frwd_box2.Add(self.pause, 0, wx.EXPAND | wx.RIGHT, 10)
        self.frwd_box2.Add(self.stop, 0, wx.EXPAND | wx.RIGHT, 5)
        for item in self.frwd_box2.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Disable()

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(file_box_sizer, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        vbox.Add(self.progress_bar, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        vbox.Add(self.settings_box_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(self.frwd_box1, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(self.frwd_box2, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        main_box_sizer.Add(vbox, 0, wx.ALIGN_CENTER | wx.ALL, 5)

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

    def on_file_change(self, event=None):
        """ Event method for preview button.
        Loads the file for 3 seconds to get a feel of the file."""
        path = self.file_name.GetValue()
        self.destination_ips = {}
        self.destination_ports = {}
        cap = pcaplib.CapFile(filename=path)

        start_time = time.time()
        self.progress_bar.Reset()
        for packet in cap:
            elapsed = time.time() - start_time
            progress = min(100, int((elapsed / 3) * 100))
            self.progress_bar.SetValue(progress)

            if elapsed > 3:
                break
            if not isinstance(packet, pcaplib.Packet):
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
        self.progress_bar.SetValue(100)
        cap.close()
        sorted_destination_ips = dict(sorted(self.destination_ips.items(), key=lambda item: len(item[1]), reverse=True))
        sorted_destination_ports = dict(sorted(self.destination_ports.items(), key=lambda item: len(item[1]), reverse=True))

        self.ip_cmb_bx.Set([f"{key} ({len(sorted_destination_ips[key])} Packets)" for key in sorted_destination_ips])
        self.ip_cmb_bx.SetSelection(0)
        self.port_cmb_bx.Set([f"{key} ({len(sorted_destination_ports[key])} Packets)" for key in sorted_destination_ports])
        self.port_cmb_bx.SetSelection(0)
        self.set_status_text("The list and packet numbers are just for getting a feel of the file, they might not include all the packets!!!")
        self.update_list()

    def update_list(self, event=None):
        """Updates the list according to the selected destination Port and IP. Does not feed the list more than 210"""
        self.list_ctrl.DeleteAllItems()
        if self.destination_ips and self.destination_ports:   # Check if there were any IP and Port scanned
            ip_key = self.ip_cmb_bx.GetStringSelection().split(" ")[0]
            port_key = self.port_cmb_bx.GetStringSelection().split(" ")[0]
            packets = self.destination_ips[ip_key]
            protocol = self.protocol_cmb_bx.GetStringSelection()
            lines = random.randint(250, 300)
            for packet in packets:
                if (protocol == 'UDP' and not packet.udp_len) or (protocol == 'TCP' and packet.udp_len):
                    continue
                if str(packet.dst_port) == port_key:
                    self.add_to_list(packet)
                if self.list_ctrl.GetItemCount() > lines:
                    break

    def on_forward(self, event):
        if self.re_transmit_thread:
            self.re_transmit_thread.playing_event.set()
            self.forward.Disable()
            self.pause.Enable()
            self.forward.SetLabel("Play Out")
            return

        dst_ip = self.dst_ip_input.GetValue()
        dst_port = self.dst_port_input.GetValue()
        rate = self.rate_input.GetValue() # Packets per second
        index = self.index_input.GetValue()
        loss = self.loss_input.GetValue()
        add_source = self.source_ck_bx.IsChecked()
        if not utils.is_valid_ip(dst_ip):
            self.error_prompt("Destination IP not valid!")
            return
        if not utils.is_valid_port(dst_port):
            self.error_prompt("Destination IP not valid!")
            return
        if not utils.is_positive_number(rate):
            self.error_prompt("Packets per second should be an integer greater than zero!")
            return
        if not utils.is_positive_number(index):
            self.error_prompt("Index should be an integer greater than zero!")
            return
        if not utils.is_percentage(loss):
            self.error_prompt("Loss should be a number <= 100 and >= 0")
            return
        self.wxconfig.Write("/forwardIP", dst_ip)
        self.wxconfig.Write("/forwardPort", dst_port)
        self.wxconfig.Write("/forwardRate", rate)
        self.wxconfig.Write("/forwardIndex", index)
        self.wxconfig.Write("/trafficController", str(add_source))
        self.wxconfig.Write("/forwardLoss", loss)
        trg_ip = self.ip_cmb_bx.GetStringSelection().split(" ")[0]
        trg_port = int(self.port_cmb_bx.GetStringSelection().split(" ")[0])
        path = self.file_name.GetValue()
        protocol = self.protocol_cmb_bx.GetStringSelection()
        self.re_transmit_thread = Threads.ReTransmitPacketsThread(path, trg_ip, trg_port, protocol, dst_ip, int(dst_port),
                                                                  add_source, int(index), int(rate), int(loss))
        self.timer.Start(200)
        self.pause.Enable()
        self.stop.Enable()
        self.forward.Disable()

    def on_pause(self, event):
        self.forward.Enable()
        if self.re_transmit_thread:
            self.re_transmit_thread.playing_event.clear()
            self.pause.Disable()
            self.forward.SetLabel("Resume")

    def on_stop(self, event):
        if self.re_transmit_thread is not None:
            self.re_transmit_thread.end_event.set()
            self.forward.SetLabel("Play Out")
            self.pause.Disable()
            self.stop.Disable()

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
           self.wxconfig.Write("/capture_path", dialog.GetPath())
           self.on_file_change()
           
           for item in self.settings_box_sizer.GetChildren():
               widget = item.GetWindow()
               if widget:
                   widget.Enable()
           for item in self.frwd_box1.GetChildren():
               widget = item.GetWindow()
               if widget:
                   widget.Enable()
           for item in self.frwd_box2.GetChildren():
               widget = item.GetWindow()
               if widget:
                   widget.Enable()
           self.pause.Disable()
           self.stop.Disable()

       dialog.Destroy()


    def set_status_text(self, text):
        self.parent.SetStatusText(text)

    def OnTimer(self, event):
        """Called periodically while the flooder threads are running."""
        count = self.re_transmit_thread.sent_count
        total = '?' if self.re_transmit_thread.total_packets == 0 else str(self.re_transmit_thread.total_packets)
        # self.set_status_text(f"Forwarding Packets{'.' * (self.animation_counter % 10)}")
        self.set_status_text(f"Forwarding Packet {count} out of {total}")
        if self.re_transmit_thread.end_event.is_set():
            if self.timer.IsRunning():
                self.timer.Stop()
            count = self.re_transmit_thread.sent_count - self.re_transmit_thread.index
            self.set_status_text(f"Forwarded {count} packets")
            self.re_transmit_thread = None
            self.forward.Enable()

    def error_prompt(self, message):
        dlg = wx.MessageDialog(self, message, "Error", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
# End class Panel(wx.Panel)


if __name__ == '__main__':
    import Main

    Main.Main()
