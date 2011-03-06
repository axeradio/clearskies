#!/usr/bin/python

"""
Clearskies: a simple DarkIce management tool
Author: Scott L. Cann 083065c@acadiau.ca
        Samuel Coleman 105709c@acadiau.ca
Version: 2011-01-11
"""

import ConfigParser
import glob
import os
import shutil
import subprocess
import time
import wx
from wx import xrc
import urllib
import urllib2
import base64

class Broadcast:
   def __init__(self, mode, filename = None):
      self.darkice = None
      self.playback = None
      self.running = False

      self.mode = mode
      self.filename = filename

   def set_filename(self, filename):
      self.filename = filename

   def start(self):
      try:
         shutil.copy("darkice_" + self.mode + ".cfg", config.get("broadcast", "configuration"))
      except IOError:
         raise Exception, "Permission error: could not replace configuration file " + config.get("broadcast", "configuration") + "!"

      self.darkice = subprocess.Popen("darkice")

      if (self.mode == "playback"):
         self.playback = subprocess.Popen(['mpg123', '-q', "--loop", "-1", self.filename])

      time.sleep(.5);

      req = urllib2.Request(config.get("icecast", "updateurl"))
      req.add_header(
         "Authorization",
         "Basic %s" % base64.encodestring(
            "%s:%s" % (
               config.get("icecast", "username"),
               config.get("icecast", "password")))[:-1])
      handle = urllib2.urlopen(req)

      self.running = True

   def stop(self):
      if (self.darkice != None):
         self.darkice.terminate()
      if (self.playback != None):
         self.playback.terminate()
      self.running = False

   def is_running(self):
      return self.running

class ClearskiesApp(wx.App):
   def OnInit(self):
      self.res = xrc.XmlResource("Clearskies.xrc")
      self.init_frame()
      return True

   def init_frame(self):
      self.broadcast = None

      self.frame = self.res.LoadFrame(None, "MainFrame")
      self.frame.SetIcon(wx.Icon("Clearskies.ico", wx.BITMAP_TYPE_ICO))

      self.about = wx.AboutDialogInfo()
      self.about.Name = "Clearskies"
      self.about.Version = "2010-11-19"
      self.about.Description = "Clearskies is simple DarkIce management tool."
      self.about.Developers = [
            "Scott L. Cann " + u'\u2013' + " 083065c@acadiau.ca",
            "Samuel Coleman  " + u'\u2013' + " 105709c@acadiau.ca"]

      self.file_picker = xrc.XRCCTRL(self.frame, "playbackFile");
      self.meta = xrc.XRCCTRL(self.frame, "meta");
      self.set_meta = xrc.XRCCTRL(self.frame, "setMeta");
      self.clear_meta = xrc.XRCCTRL(self.frame, "clearMeta");
      self.live = xrc.XRCCTRL(self.frame, "live");
      self.live_runtime = xrc.XRCCTRL(self.frame, "liveRuntime");
      self.playback_runtime = xrc.XRCCTRL(self.frame, "playbackRuntime");
      self.mode_selector = xrc.XRCCTRL(self.frame, "modeSelector");

      self.live_starttime = time.time()
      self.live_timer = wx.Timer(self.frame)
      self.playback_starttime = time.time()
      self.playback_timer = wx.Timer(self.frame)

      self.update_file()

      self.frame.Bind(wx.EVT_MENU, self.on_exit, id=xrc.XRCID("exit"))
      self.frame.Bind(wx.EVT_MENU, self.on_fixpermissions, id=xrc.XRCID("fixPermissions"))
      self.frame.Bind(wx.EVT_MENU, self.on_about, id=xrc.XRCID("about"))
      self.frame.Bind(wx.EVT_BUTTON, self.on_set_meta, id=xrc.XRCID("setMeta"))
      self.frame.Bind(wx.EVT_BUTTON, self.on_clear_meta, id=xrc.XRCID("clearMeta"))
      self.frame.Bind(wx.EVT_TOGGLEBUTTON, self.on_live, id=xrc.XRCID("live"))
      self.frame.Bind(wx.EVT_TIMER, self.on_live_timer, self.live_timer)
      self.frame.Bind(wx.EVT_TIMER, self.on_playback_timer, self.playback_timer)

      self.mode_selector.SetSelection(0)
      self.on_live(wx.EVT_TOGGLEBUTTON)

      self.frame.Show()

   def on_exit(self, evt):
      self.frame.Destroy()

   def OnExit(self):
      if (self.broadcast != None):
         self.broadcast.stop()
      self.live_timer.Stop()
      self.playback_timer.Stop()

   def on_about(self, evt):
      wx.AboutBox(self.about)

   def on_set_meta(self, evt):
      req = urllib2.Request(config.get("icecast", "updateurl") + urllib.quote_plus(self.meta.GetValue()))
      req.add_header(
         "Authorization",
         "Basic %s" % base64.encodestring(
            "%s:%s" % (
               config.get("icecast", "username"),
               config.get("icecast", "password")))[:-1])
      handle = urllib2.urlopen(req)
      error = wx.MessageDialog(self.frame, "Meta information set.", "Meta", wx.OK)
      error.ShowModal()
      error.Destroy()
   
   def on_clear_meta(self, evt):
      req = urllib2.Request(config.get("icecast", "updateurl"))
      req.add_header(
         "Authorization",
         "Basic %s" % base64.encodestring(
            "%s:%s" % (
               config.get("icecast", "username"),
               config.get("icecast", "password")))[:-1])
      handle = urllib2.urlopen(req)
      self.meta.SetValue("")
      error = wx.MessageDialog(self.frame, "Meta information cleared.", "Meta", wx.OK)
      error.ShowModal()
      error.Destroy()

   def on_live(self, evt):
      if (self.live.GetValue() == True):
         if (self.mode_selector.GetSelection() == 0):
            self.broadcast = Broadcast("live")

            self.live_runtime.SetLabel("00:00:00")
            self.live_starttime = time.time()
            self.current_timer = self.live_timer
         else:
            self.broadcast = Broadcast("playback", self.file_picker.GetPath())

            self.playback_runtime.SetLabel("00:00:00")
            self.playback_starttime = time.time()
            self.current_timer = self.playback_timer

         try:
            self.broadcast.start()

            self.current_timer.Start(1000)

            self.live.SetLabel("Live!")
            self.live.SetForegroundColour("red")

            self.meta.SetValue("")
         except Exception as e:
            self.broadcast.stop()
            self.live_timer.Stop()
            self.playback_timer.Stop()
            self.live.SetValue(False)
            self.live.SetLabel("Go Live");
            self.live.SetForegroundColour("default")

            error = wx.MessageDialog(self.frame, str(e), "Error", wx.OK)
            error.ShowModal()
            error.Destroy()
      else:
         if (self.broadcast != None):
            confirmation = wx.MessageDialog(self.frame, "Are you sure you wish to stop broadcasting?", "Confirmation", wx.YES | wx.NO | wx.ICON_EXCLAMATION)
            if (confirmation.ShowModal() == wx.ID_YES):
               self.broadcast.stop()

               self.live_timer.Stop()
               self.playback_timer.Stop()

               self.live.SetLabel("Go Live");
               self.live.SetForegroundColour("default")

               self.update_file()
            else:
               self.live.SetValue(True)
            confirmation.Destroy()

   def on_live_timer(self, evt):
      runtime = int(time.time() - self.live_starttime)
      self.live_runtime.SetLabel("%02d:%02d:%02d" % (runtime / 3600, runtime / 60, runtime % 60))

   def on_playback_timer(self, evt):
      runtime = int(time.time() - self.playback_starttime)
      self.playback_runtime.SetLabel("%02d:%02d:%02d" % (runtime / 3600, runtime / 60, runtime % 60))

   def update_file(self):
      directory = os.getcwd()
      try:
         directory = config.get("playback", "directory")
      except:
         error = wx.MessageDialog(self.frame, "Configuration error: could not locate playback directory! Assuming current directory as playback directory.", "Configuration error", wx.OK)
         error.ShowModal()
         error.Destroy()
      files = [(os.path.getmtime(x), x) for x in glob.glob(os.path.abspath(directory) + "/*.mp3")]
      files.sort()
      if (len(files) > 0):
         self.file_picker.SetPath(files[-1][1])

   def on_fixpermissions(self, evt):
      os.system("python fixperms.py")
      message = wx.MessageDialog(self.frame, "Permissions updated. ", "Permissions Utility", wx.OK)
      message.ShowModal()
      message.Destroy()

if __name__ == "__main__":
   config = ConfigParser.ConfigParser()
   config.read("Clearskies.ini")
   app = ClearskiesApp(False)
   app.MainLoop()
