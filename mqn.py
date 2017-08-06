# a mqtt desktop notifier
# author: Blake Oliver <oliver22213@me.com>

import json
import os
from socket import gethostname
import webbrowser
import wx
from wx import App
from wx.adv import TaskBarIcon
from paho.mqtt import client
import pytoml
import certifi
import utils
from constants import default_config, connect_codes



class Mqn(TaskBarIcon):
    def __init__(self, icon_name):
        super(Mqn, self).__init__()
        self.mqtt_connected = False
        self.mqtt_loop_running = False
        self.icon_name = icon_name
        self.SetIcon(wx.NullIcon, self.icon_name)
        self.setup_config()
        self.client = client.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.mqtt_connect()

    def setup_config(self):
        self.user_config, self.config_file = utils.get_config()
        # config checks...
        if self.user_config == None:
            m = wx.MessageDialog(parent=None, caption="No configuration file found", message="No configuration could be found for Mqn. Please create one and run this program again.")
            m.ShowModal()
            self.on_exit()
            return
        self.config = utils.combine_config(self.user_config, default_config)
        if self.config.get('mqtt', None) == None:
            m = wx.MessageDialog(parent=None, caption="Missing mqtt options", message="There is no 'mqtt' section in the configuration file.\nPlease specify one with your desired options and run this program again.")
            m.ShowModal()
            self.on_exit()
            return
        if self.config['mqtt'].get('host', None) == None:
            m = wx.MessageDialog(parent=None, caption="No mqtt host specified", message="An mqtt host wasn't specified in the configuration file.\nPlease specify one and run this program again.")
            m.ShowModal()
            self.on_exit()
            return
        if self.config.get('topic', None) == None:
            m = wx.MessageDialog(parent=None, caption="No notification topics in config", message="No notification topics have been specified in the configuration file.\nYou must specify at least one topic for mqn to subscribe to.\nPlease do so, and then restart this program.")
            m.ShowModal()
            self.on_exit()
            return

    def mqtt_connect(self):
        """Establishes a connection to the mqtt broker specified in config, sets up subscription message handlers for all the specified topics, and starts the event processing loop for mqtt."""
        if self.config['mqtt'].get('username', None) != None:
            if self.config['mqtt'].get('password', None) == None: # no password, just a username
                self.client.username_pw_set(self.config['mqtt']['username'])
            else: # username and pw
                self.client.username_pw_set(self.config['mqtt']['username'], self.config['mqtt']['password'])
        if self.config['mqtt']['ssl'] == True: # ssl is enabled for this broker connection
            tls = {}
            if self.config['mqtt']['ca_certs'].lower() == "auto":
                tls['ca_certs'] = certifi.where()
            if self.config['mqtt'].get('certfile', None) != None:
                tls['certfile'] = self.config['mqtt']['certfile']
            if self.config['mqtt'].get('keyfile', None) != None:
                tls['keyfile'] = self.config['mqtt']['keyfile']
            self.client.tls_set(**tls)
        for sub in self.config['topic'].iterkeys():
            self.client.message_callback_add(sub, self.on_notification)
        self.client.connect(self.config['mqtt']['host'], self.config['mqtt']['port'], self.config['mqtt']['keepalive'])
        self.client.loop_start()


    def on_connect(self, c, u, f, r):
        if r in connect_codes.keys():
            self.set_status(connect_codes[r])
            if r > 0:
                self.client.disconnect()
                self.client.loop_stop()
                self.ShowBalloon("Connection failed to {}".format(self.config['mqtt']['host']), connect_codes[r])
        else: # given code is unknown
            self.set_status("connection refused (reason unknown)")
        if r == 0:
            self.mqtt_connected = True
            subs = self.config['topic']
            for s in subs.iterkeys():
                self.client.subscribe(s, subs[s].get('qos', 0))

    def on_disconnect(self, c, u, r):
        if r > 0:
            self.set_status("disconnected unexpectedly, reconnecting soon")
        else:
            self.mqtt_connected = True
            self.set_status("disconnected")

    def on_notification(self, c, u, msg):
        try:
            m = json.loads(msg.payload)
            if m.get('type', None) == 'notification' and m.get('title', False) and m.get('message', False):
                self.ShowBalloon(m['title'], m['message'])
        except ValueError as e:
            pass # not a valid mqn message

    def CreatePopupMenu(self):
        menu = wx.Menu()
        utils.create_menu_item(menu, "open configuration file", self.open_config)
        utils.create_menu_item(menu, "&reload configuration file", self.reload_config)
        utils.create_menu_item(menu, "open mqn &website", self.open_website)
        utils.create_menu_item(menu, "e&xit", self.on_exit)
        return menu

    def set_status(self, status=""):
        """Method that sets a small status message next to the icon's name in the system tray.
If status is an empty string (which is the default), then set the name of the icon to what this class was instantiated with.
        """
        if status == '':
            self.SetIcon(wx.NullIcon, self.icon_name)
        else:
            self.SetIcon(wx.NullIcon, """{}: {}""".format(self.icon_name, status))

    def open_website(self, event=None):
        webbrowser.open("https://github.com/oliver2213/mqn")

    def open_config(self, event=None):
        os.startfile(self.config_file)

    def reload_config(self, event=None):
        # this is pretty useless until I make the program reconnect after a reload
        self.setup_config()
        wx.MessageDialog(parent=None, caption="config reloaded", message="The configuration file has been reloaded.").ShowModal()

    def on_exit(self, event=None):
        wx.CallAfter(self.Destroy)

def main():
    m = None
    app = App()
    try:
        m = Mqn("mqn")
        app.MainLoop()
    except Exception as e:
        #print("""Unhandled exception:\n{}""".format(str(e)))
        raise
        wx.MessageDialog(parent=None, caption="Error!", message="""{}: {}""".format(e.__class__, e)).ShowModal()
        return
    finally:
        # gracefully disconnect, even if an exception is thrown
        if m != None and getattr(m, 'client', False):
            m.client.disconnect()


if __name__ == '__main__':
    main()