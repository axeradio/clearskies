#!/usr/bin/python

"""
Permissions utility for Clearskies. Automagically chown/chmods any MP3s in the
darkice dump directory given in the configuration.
Author: Samuel Coleman 105709c@acadiau.ca
Version: 2011-01-11
"""

import ConfigParser
import glob
import os
import wx

def fix_permissions():
   files = glob.glob(os.path.abspath(config.get("playback", "directory")) + "/*.mp3")
   for file in files:
      os.chown(file, int(config.get("system", "user")), int(config.get("system", "group")))
      os.chmod(file, 0644)

if __name__ == "__main__":
   config = ConfigParser.ConfigParser()
   config.read("Clearskies.ini")
   fix_permissions()