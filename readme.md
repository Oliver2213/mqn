# mqn -a mqtt notifier

This is a small program to send notifications (via the system tray) based on messages sent to a configurable list of topics on a mqtt server.

## config
The configuration format for this program is TOML, which is similar to the ubiquitous ini format. An example config file is below, with the meanings of the various options as comments:

```
# options not marked as required can be left out of your config, and a reasonable default will be used if one is required

# mqn options (which affect how the program itself behaves)
[mqn]

# don't send notifications to the system tray for events like connecting to and disconnecting from the mqtt broker unless an error is encountered. this does not affect notifications mqn receives through mqtt.
# if this is set to false, you'll get notifications whenever these things happen.
quiet = true

# upon startup, automatically connect to the configured mqtt broker.
# If this is set to false, you will need to manually tell mqn to connect to your mqtt broker via the system tray menu.
autoconnect = true

# if there's a base topic all notification messages will be sent to, specify it here.
# You can still specify any number of other topics, but if there is one topic a majority of messages will be sent to, use this option.
# This option doesn't have a default value, so if you don't specify it in your config, it won't assume anything
base_topic = "notifications"

# Whether or not to subscribe to a topic with the name of the machine mqn is running on.
# This uses base_topic, so with a machine name of "some-machine," and a base_topic of "notifications", mqn will subscribe to "notifications/some-machine".
# This allows you to send notifications to any machine, as long as you know it's name and it's online.
directed_notifications = false

# mqtt options
[mqtt]

# the host of your mqtt broker (required).
host = "someserver.com"

# the port on which it is listening.
# 1883 is the default for mqtt; 8883 is for mqtt over ssl.
port=8883

# the ping keep-alive between this program and your mqtt broker.
keepalive = 60 # in seconds

# if your broker uses username and password authentication, specify them here.
username = "myuser"
password = "passwordhere"

# these values control the minimum and maximum amount of time the program will use between reconnects.
min_reconnect_delay = 1
max_reconnect_delay = 120

# if your broker uses ssl to protect it's traffic (which it really should), set this to true (and configure any other ssl options you need), otherwise set this to false or leave it out entirely.
# if this is set to false, ssl will not be applied to the connection to your broker, regardless of whether you have the below ssl options set
ssl = true

# a path to a pem-encoded file containing certificate authority certificates; if this is left out or set to "auto", the mozilla bundle is used.
ca_certs = "auto"

# if this program should authenticate with an ssl certificate, set these options to the paths you want.
# ideally these shouldn't be password-protected, because ssl will ask for it on the command line; I might add support for a UI prompt for this later.
certfile = 'C:\users\you\ssl_cert.pem' # note the use of '; use it when writing windows paths so backslashes are treated normally
keyfile = 'C:\users\you\ssl_key.pem'

# at least one topic section is required.
# each topic is in it's own table, defined like [topic."your/topic/here"].
# note that you must put the topic name in  quotes, like the following.
[topic."notifications/laptop"]
# you can leave a topic section empty,
# or specify a qos (quality of service), which goes from 0 (no acknowledgment of messages) to 2 (make super sure that this client gets every message).
# qos 0 is the default.

# you can also specify multiple topics, including wildcards
# as long as your broker grants you access to what you try to subscribe to.
#[topic."notifications/#"]
qos = 1
[topic."mqn/+"]

```

## Notification message format
For a message sent to a configured topic to be considered a notification by mqn, it needs to use the following json format:

```
{
  "type" : "notification",
  "title" : "Notification Title",
  "message" : "This is a notification message.",
}
```

Any other message format is silently ignored.