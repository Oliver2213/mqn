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
        self.mqtt_connection_is_set_up = False
        self.mqtt_connected = False
        self.mqtt_loop_running = False
        self.icon_name = icon_name
        self.SetIcon(wx.NullIcon, self.icon_name)
        self.setup_config()
        self.client = client.Client()
        self.mqtt_setup_connection()
        if self.config['mqn']['autoconnect'] == True:
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

    def mqtt_setup_connection(self, force=False, reload=False):
        """Configures the mqtt broker connection with options set in config (host, port, ssl and specific args, username and pw)."""
        if self.mqtt_connection_is_set_up == False or force==True:
            if reload==True: 
                self.client.reinitialise() # is it me or is that misspelled 
            self.mqtt_loop_check()
            if self.mqtt_loop_running == True or self.mqtt_connected == True:
                self.mqtt_disconnect()
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
            self.mqtt_connection_is_set_up = True

    def mqtt_connect(self, start_loop=True):
        """Establishes a connection to the mqtt broker specified in config, sets up subscription message handlers for all the specified topics, and starts the event processing loop for mqtt."""
        if self.mqtt_connection_is_set_up == False:
            self.mqtt_setup_connection()
        if self.client.on_connect==None or self.client.on_disconnect==None:
            self.mqtt_set_callbacks()
        if self.mqtt_connected or self.mqtt_loop_running:
            self.mqtt_disconnect()
        self.client.connect(self.config['mqtt']['host'], self.config['mqtt']['port'], self.config['mqtt']['keepalive'])
        if start_loop:
            self.client.loop_start()
            self.mqtt_loop_running = True

    def mqtt_loop_check(self):
        """Check to see if the mqtt event loop is alive, and set the value that reflects this on the class instance."""
        # maybe make this a property so checking self.mqtt_loop_running will run this?
        if getattr(self.client, '_thread', False) == False or self.client._thread == None: # the thread doesn't exist
            self.mqtt_loop_running = False
        else: # a thread does exist, determine it's running status
            self.mqtt_loop_running = self.client._thread.is_alive()

    def mqtt_set_callbacks(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def mqtt_disconnect(self):
        """Disconnect from the mqtt broker if we're connected, and stop the mqtt event loop if it's running."""
        if self.mqtt_connected:
            self.client.disconnect()
        self.mqtt_loop_check()
        if self.mqtt_loop_running:
            self.client.loop_stop()
            self.mqtt_loop_running = False

    def on_connect(self, c, u, f, r):
        if r in connect_codes.keys():
            self.set_status(connect_codes[r])
            if r > 0:
                self.mqtt_disconnect()
                self.ShowBalloon("Connection failed to {}".format(self.config['mqtt']['host']), connect_codes[r])
        else: # given code is unknown
            self.mqtt_disconnect() # the previous call to this method only applies if the return code is from 0 to 5 (as there are no other codes on the constants dict)
            self.set_status("connection refused (reason unknown)")
            self.ShowBalloon(title="Connection refused", text="The connection to {} was refused (reason unknown)".format(self.config['mqtt']['host']))
        if r == 0:
            self.mqtt_connected = True
            subs = self.config['topic']
            for s in subs.iterkeys():
                self.client.subscribe(s, subs[s].get('qos', 0))
        if self.config['mqn']['quiet'] == False:
            self.ShowBalloon(title="Connected to mqtt broker", text="Connection established to {}".format(self.config['mqtt']['host']))
        self.mqtt_loop_check()

    def on_disconnect(self, c, u, r):
        if r > 0:
            self.set_status("disconnected unexpectedly, reconnecting soon")
            if self.config['mqn']['quiet'] == False:
                self.ShowBalloon(title="Unexpectedly disconnected from {}".format(self.config['mqtt']['host']), text="Connection to the mqtt broker has been lost; trying to reconnect soon.")
        else:
            self.mqtt_connected = False
            self.set_status("disconnected")
            if self.config['mqn']['quiet'] == False:
                self.ShowBalloon(title="Disconnected from mqtt broker", text="disconnected from {}".format(self.config['mqtt']['host']))
        self.mqtt_loop_check()

    def on_notification(self, c, u, msg):
        try:
            m = json.loads(msg.payload)
            if m.get('type', None) == 'notification' and m.get('title', False) and m.get('message', False):
                self.ShowBalloon(m['title'], m['message'])
        except ValueError as e:
            pass # not a valid mqn message

    def CreatePopupMenu(self):
        menu = wx.Menu()
        utils.create_menu_item(menu, "connect", self.do_menu_connect, kind=wx.ITEM_CHECK).Check(self.mqtt_connected) # if we're connected to the broker, this is checked
        utils.create_menu_item(menu, "open configuration file", self.open_config)
        utils.create_menu_item(menu, "&reload configuration file", self.reload_config)
        utils.create_menu_item(menu, "open mqn &website", self.open_website)
        utils.create_menu_item(menu, "e&xit", self.on_exit)
        return menu

    def set_status(self, status=""):
        """Method that sets a small status message next to the icon's name in the system tray.
If status is an empty string (which is the default), then set the name of the icon to what this class was instantiated with.
        """
        try:
            if status == '':
                self.SetIcon(wx.NullIcon, self.icon_name)
            else:
                self.SetIcon(wx.NullIcon, """{}: {}""".format(self.icon_name, status))
        except RuntimeError as e:
            pass

    def do_menu_connect(self, event=None):
        """Connect or disconnect from the configured mqtt broker."""
        # no matter what the menu item's checked status says, this method will properly open or close a connection to the configured broker
        # I do it this way because (unlikely though it is), the connection status can change while a menu is open;
        # so if this method acts based on that, it could run connect (when there is already one established), and cause a reconnect, which would require another usage of this method to fix
        # or it could run disconnect, when there is no connection to the broker, thus doing nothing
        if self.mqtt_connected == True: # disconnect
            self.mqtt_disconnect()
        elif self.mqtt_connected == False: # connect
            self.mqtt_connect()

    def open_website(self, event=None):
        webbrowser.open("https://github.com/oliver2213/mqn")

    def open_config(self, event=None):
        os.startfile(self.config_file)

    def reload_config(self, event=None):
        self.setup_config()
        # disconnect if necessary, stop the mqtt event loop, reset settings from config, and reconnect again
        self.mqtt_disconnect()
        self.mqtt_setup_connection(force=True, reload=True)
        if self.config['mqn']['autoconnect'] == True:
            self.mqtt_connect()
        wx.MessageDialog(parent=None, caption="config reloaded", message="The configuration file has been reloaded and the connection to your configured mqtt broker is being reestablished according to the updated config.").ShowModal()

    def on_exit(self, event=None):
        self.mqtt_disconnect() # will only disconnect if it needs doing, and stops mqtt's loop as well if necessary
        wx.CallAfter(self.Destroy)

def main():
    m = None
    app = App()
    try:
        m = Mqn("mqn")
        app.MainLoop()
    except Exception as e:
        #print("""Unhandled exception:\n{}""".format(str(e)))
        #raise
        wx.MessageDialog(parent=None, caption="Error!", message="""{}: {}""".format(type(e).__name__, e)).ShowModal()
        return
    finally:
        # gracefully disconnect, even if an exception is thrown
        if m != None and getattr(m, 'client', False) and m.mqtt_connected==True: # if there is an mqn object, if it has an mqtt client, and it indicates that it is still connected to a broker
            m.mqtt_disconnect()


if __name__ == '__main__':
    main()