# utilities

import os
import sys
import wx
import appdirs
import pytoml as toml

def create_menu_item(menu, label, func, id=None, help="", kind=wx.ITEM_NORMAL):
    """A quick function to add and bind a menu item.
            The point of this is to provide a wrapper around WX and be called by the application with all the arguments it needs (and with defaults that you can just not worry about if you don't need them). It will also handle binding to a menu event.
            This can be used for menubars, system tray icons, etc.
            Necessary info is the menu object in question, a label for your new option, and a funcion you'd like to bind it to. You can also provide a help text, the kind, and an ID, if your making a stock item (about, exit, new), it's best to use those so they look native on every OS.
            Kind can be one of:
                    wx.ITEM_SEPARATOR - a line in the menu separating items
                    wx.ITEM_NORMAL - a normal clickable menu item (this is what is used if you don't specify a kind)
                    wx.ITEM_CHECK - a checkable menu item, use item.Check(True), or item.Check(False) to control this
                    wx.ITEM_RADIO - (I think...), an item that is exclusively checked. (You have 5 items, you can only have one checked)
            By default, this function appends your item to the end of the menu, so the order in which you add items by calling this function is important to how the menu looks.
            Also, remember you can denote a shortcut key with the and (&) sign before the letter in the label.
            Coppied and slightly modified from http://stackoverflow.com/questions/6389580/quick-and-easy-trayicon-with-python
    """
    if id is None:
        id = wx.ID_ANY
    item = wx.MenuItem(menu, id, label, help, kind)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

def get_config(author_name='oliver2213', app_name='mqn'):
    confname = app_name+".conf"
    # dir is a path to files included with the application, and should work whether or not the app is bundled
    if getattr(sys, 'frozen', False):
        # we are frozen
        dir = sys._MEIPASS
    else:
        dir = os.path.dirname(os.path.abspath(__file__))
    # check the working directory for a config first
    if os.path.exists(os.path.join(os.getcwd(), confname)) and os.path.isfile(os.path.join(os.getcwd(), confname)):
        with open(os.path.join(os.getcwd(), confname), 'r') as f:
            config = toml.load(f)
        return config, os.path.join(os.getcwd(), confname) # return the configuration in the current working directory
    # then check the user's config directory
    ucd = appdirs.AppDirs(appname=app_name, appauthor=author_name).user_config_dir
    if os.path.exists(os.path.join(ucd, confname)) and os.path.isfile(os.path.join(ucd, confname)):
        with open(os.path.join(ucd, confname), 'r') as f:
            config = toml.load(f)
        return config, os.path.join(ucd, confname)
    # then check the program directory (if running from source, this will be the directory containing this program; if bundled, it will be the directory of the bundle or the temp directory for an one-file bundle)
    if os.path.exists(os.path.join(dir, confname)) and os.path.isfile(os.path.join(dir, confname)):
        with open(os.path.join(dir, confname), 'r') as f:
            config = toml.load(f)
        return config, os.path.join(dir, confname) # from app directory
    # if none of that worked
    return None, None # no config found

def combine_config(user, default):
    """This method adds any default config options that are missing to the user config, and returns the dictionary."""
    # currently supports nesting only the first level of dictionaries
    # I feel like this could be written a lot better but....
    default_config = dict(**default)
    user_config = dict(**user)
    for k in default_config.iterkeys():
        if user_config.get(k, None) == None:
            user_config[k] = default_config[k]
        else: # that dict already exists, check and make sure it's values do as well
            if type(user_config[k]) == dict:
                for k2 in default_config[k].iterkeys():
                    if user_config[k].get(k2, None) == None:
                        user_config[k][k2] = default_config[k][k2]
    return user_config