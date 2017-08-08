# constants

default_config = {
 "mqn": {
  "quiet": True,\
  "autoconnect": True,\
  "directed_notifications": False,\
 },\
 "mqtt" : {
  "port" : 1883,\
  "keepalive" : 60,\
  "min_reconnect_delay" : 1,\
  "max_reconnect_delay" : 120,\
  "ssl" : False,\
  "ca_certs" : "auto",\
 }
}

connect_codes = {
 0: "connected",\
 1: "connection refused (incorrect protocol version)",\
 2: "connection refused (invalid client ID)",\
 3: "connection refused (server unavailable)",\
 4: "connection refused (incorrect username or password)",\
 5: "connection refused (not authorized)",\
}