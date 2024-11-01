import random
import socket
import time
import wx.lib.intctrl
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

        self.file_label = wx.StaticText(self, label="Capture File:")
        self.file_name = wx.TextCtrl(self, style=wx.TE_READONLY, size=(400, -1))
        self.choose_file = wx.Button(self, label="Choose File")
        self.choose_file.Bind(wx.EVT_BUTTON, self.on_choose)
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

        dst_ip_label = wx.StaticText(self, label="Destination IP:")
        self.dst_ip_input = wx.TextCtrl(self, value=self.wxconfig.Read('/forwardIP', defaultVal=""),
                                        size=(100, -1))

        dst_port_label = wx.StaticText(self, label="Destination Port:")
        self.dst_port_input = wx.TextCtrl(self, value=self.wxconfig.Read('/forwardPort', defaultVal=""),
                                      size=(50, -1))

        self.packet_loss = wx.CheckBox(self, label="Packet Loss")
        self.packet_loss.Bind(wx.EVT_CHECKBOX, self.update_checkbox_state)
        self.loss_input = wx.SpinCtrl(self, value=self.wxconfig.Read('/forwardLoss', defaultVal=""),
                                      size=(60, -1))
        self.percent_lbl = wx.StaticText(self, label="%")


        self.rate_chk_bx = wx.CheckBox(self, label="Realtime")
        self.rate_chk_bx.Bind(wx.EVT_CHECKBOX, self.update_checkbox_state)
        self.rate_input = wx.lib.intctrl.IntCtrl(self, value= int(self.wxconfig.Read('/forwardRate', defaultVal="0")),
                                          size=(40, -1))
        self.rate_label = wx.StaticText(self, label="Packets/sec")

        self.source_ck_bx = wx.CheckBox(self, label="Syslog Traffic Controller Tagging")
        self.source_ck_bx.SetToolTip("Prefixes the payload with actual packet source (::dst-ip::xxxx)")
        chk_bx_val = self.wxconfig.Read('/trafficController', defaultVal="")
        if chk_bx_val == "True":
            self.source_ck_bx.SetValue(True)

        index_label = wx.StaticText(self, label="Start Index:")
        self.index_input = wx.lib.intctrl.IntCtrl(self, value=int(self.wxconfig.Read('/forwardIndex', defaultVal="")), size=(60, -1))
        self.forward = wx.Button(self, label="Play Out")
        self.forward.Bind(wx.EVT_BUTTON, self.on_forward)
        self.pause = wx.Button(self, label="Pause")
        self.pause.Bind(wx.EVT_BUTTON, self.on_pause)
        self.stop = wx.Button(self, label="Stop")
        self.stop.Bind(wx.EVT_BUTTON, self.on_stop)
        btns = [self.forward, self.stop, self.pause]
        for btn in btns:
            btn.Disable()

        # List Control
        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.list_ctrl.InsertColumn(0, 'Index', width=50)
        self.list_ctrl.InsertColumn(1, 'Source', width=100)
        self.list_ctrl.InsertColumn(2, 'Destination', width=100)
        self.list_ctrl.InsertColumn(3, 'Length', width=50)
        self.list_ctrl.InsertColumn(4, 'Info',width=800)

        self.main_vbox = wx.BoxSizer(wx.VERTICAL)
        main_box = wx.StaticBox(self)
        main_box.SetFont(wx.Font(wx.FontInfo(12).Bold()))

        self.file_grid = wx.GridBagSizer()
        self.file_grid.Add(self.file_label, pos=(0,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)
        self.file_grid.Add(self.file_name, pos=(0,1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)
        self.file_grid.Add(self.choose_file, pos=(0,2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)

        label_flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT
        input_flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.RIGHT
        button_flag = wx.ALIGN_CENTER_VERTICAL | wx.CENTER | wx.RIGHT | wx.LEFT
        self.settings_grid1 = wx.GridBagSizer()
        self.settings_grid1.Add(trg_ip_label, pos=(0,0), flag=label_flag, border=5)
        self.settings_grid1.Add(self.ip_cmb_bx, pos=(0,1), flag=input_flag, border=15)
        self.settings_grid1.Add(trg_port_label, pos=(0,2), flag=label_flag, border=5)
        self.settings_grid1.Add(self.port_cmb_bx, pos=(0,3), flag=input_flag, border=20)
        self.settings_grid1.Add(self.protocol_cmb_bx, pos=(0,4), flag=input_flag, border=5)

        self.settings_grid2= wx.GridBagSizer()
        self.settings_grid2.Add(dst_ip_label, pos=(0,0), flag=label_flag, border=5)
        self.settings_grid2.Add(self.dst_ip_input, pos=(0,1), flag=input_flag, border=15)
        self.settings_grid2.Add(dst_port_label, pos=(0,2), flag=label_flag, border=5)
        self.settings_grid2.Add(self.dst_port_input, pos=(0,3), flag=input_flag, border=15)
        self.settings_grid2.Add(self.packet_loss, pos=(0,4), flag=label_flag)
        self.settings_grid2.Add(self.loss_input, pos=(0,5), flag=input_flag, border=5)
        self.settings_grid2.Add(self.percent_lbl, pos=(0, 6), flag=input_flag, border=5)

        self.settings_grid3 = wx.GridBagSizer()
        self.settings_grid3.Add(self.rate_chk_bx, pos=(0, 1), flag=label_flag, border=0)
        self.settings_grid3.Add(self.rate_input, pos=(0, 2), flag=label_flag, border=3)
        self.settings_grid3.Add(self.rate_label, pos=(0, 3), flag=input_flag, border=20)
        self.settings_grid3.Add(self.source_ck_bx, pos=(0,4), flag=input_flag, border=15)
        self.settings_grid3.Add(index_label, pos=(0,5), flag=label_flag, border=5)
        self.settings_grid3.Add(self.index_input, pos=(0,6), flag=input_flag, border=15)

        self.settings_grid4 = wx.GridBagSizer()
        self.settings_grid4.Add(self.forward, pos=(0, 4), flag=button_flag, border=5)
        self.settings_grid4.Add(self.pause, pos=(0, 5), flag=button_flag, border=5)
        self.settings_grid4.Add(self.stop, pos=(0, 6), flag=button_flag, border=5)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.file_grid, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        vbox.Add(self.progress_bar, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        vbox.Add(self.settings_grid1, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(self.settings_grid2, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(self.settings_grid3, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(self.settings_grid4, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.main_vbox.Add(vbox, flag= wx.ALIGN_CENTER | wx.ALL, border=5)
        self.main_vbox.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(self.main_vbox)
        self.disable_settings()

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
        self.forward.Enable()
        self.enable_settings()
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
        dst_ip = self.dst_ip_input.GetValue()
        dst_port = self.dst_port_input.GetValue()
        rate = -1 if self.rate_chk_bx.IsChecked() else self.rate_input.GetValue() # Packets per second
        index = self.index_input.GetValue()
        loss = self.loss_input.GetValue() if self.packet_loss.IsChecked() else 0
        add_source = self.source_ck_bx.IsChecked()

        if not utils.is_valid_ip(dst_ip):
            self.error_prompt("Destination IP not valid!")
            return
        if not utils.is_valid_port(dst_port):
            self.error_prompt("Destination IP not valid!")
            return
        if rate < -1:
            self.error_prompt("Invalid Packets per second!")
            return
        if not utils.is_positive_number(index):
            self.error_prompt("Index should be an integer greater than zero!")
            return
        self.wxconfig.Write("/forwardIP", dst_ip)
        self.wxconfig.Write("/forwardPort", dst_port)
        if rate != -1:
            self.wxconfig.Write("/forwardRate", str(rate))
        self.wxconfig.Write("/forwardIndex", str(index))
        self.wxconfig.Write("/trafficController", str(add_source))
        self.wxconfig.Write("/forwardLoss", str(loss))
        trg_ip = self.ip_cmb_bx.GetStringSelection().split(" ")[0]
        trg_port = int(self.port_cmb_bx.GetStringSelection().split(" ")[0])
        path = self.file_name.GetValue()
        protocol = self.protocol_cmb_bx.GetStringSelection()

        if self.re_transmit_thread:  # this is used as a resume button and change settings
            self.re_transmit_thread.playing_event.set()
        else:
            self.re_transmit_thread = Threads.ReTransmitPacketsThread(path, trg_ip, trg_port, protocol, dst_ip, int(dst_port),
                                                                  add_source, int(index), int(rate), loss)
            self.timer.Start(500)
        self.disable_settings()
        for item in self.file_grid.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Disable()
        self.pause.Enable()
        self.stop.Enable()
        self.forward.Disable()
        self.forward.SetLabel("Play Out")

    def on_pause(self, event):
        if self.re_transmit_thread:
            self.forward.Enable()
            self.forward.SetFocus()
            self.re_transmit_thread.playing_event.clear()
            self.pause.Disable()
            self.forward.SetLabel("Resume")

    def update_checkbox_state(self, event=None):
        if self.packet_loss.IsChecked():
            self.loss_input.Enable()
            self.percent_lbl.Enable()
        else:
            self.loss_input.Disable()
            self.percent_lbl.Disable()

        if self.rate_chk_bx.IsChecked():
            self.rate_label.Disable()
            self.rate_input.Disable()
        else:
            self.rate_label.Enable()
            self.rate_input.Enable()

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
           self.pause.Disable()
           self.stop.Disable()

       dialog.Destroy()

    def disable_settings(self):
        for item in self.settings_grid1.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Disable()
        for item in self.settings_grid2.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Disable()
        for item in self.settings_grid3.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Disable()

    def enable_settings(self):
        for item in self.settings_grid1.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Enable()
        for item in self.settings_grid2.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Enable()
        for item in self.settings_grid3.GetChildren():
            widget = item.GetWindow()
            if widget:
                widget.Enable()
        self.update_checkbox_state()

    def set_status_text(self, text):
        self.parent.SetStatusText(text)

    def OnTimer(self, event):
        """Called periodically while the flooder threads are running."""
        count = self.re_transmit_thread.sent_count
        total = '?' if self.re_transmit_thread.total_packets == 0 else str(self.re_transmit_thread.total_packets)
        self.set_status_text(f"Forwarding Packet {count} out of {total}")
        if self.re_transmit_thread.end_event.is_set():
            self.enable_settings()
            for item in self.file_grid.GetChildren():
                widget = item.GetWindow()
                if widget:
                    widget.Enable()
                self.pause.Disable()
                self.stop.Disable()
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
