import wx


class ProgressBarWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_value = 0
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.progress = wx.Gauge(self, range=100, size=(600, 5))
        vbox.Add(self.progress, 0, wx.ALL | wx.EXPAND, 10)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER)
        self.SetSizer(vbox)

    def Reset(self):
        """Reset the progress bar to 0"""
        self.current_value = 0
        self.progress.SetValue(0)

    def SetValue(self, value):
        """Set progress value (0-100)"""
        self.current_value = value
        self.progress.SetValue(self.current_value)