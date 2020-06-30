# AppDynamics control tool
AppDCTL is aimed to control and maintain an AppDynamics controller configuration.
In order to establish a connection to an AppDynamics controller, please login first.

# Required packages
	python python-requests python-libxml2

# appdconfig.yaml file format
contexts:
- context:
    server: <protocol>://<ip>:<port>
    user: <username>/<ip>:<port>
  name: <ip>:<port>/<username>
current-context: <ip>:<port>/<username>
users:
- name: <username>/<ip>:<port>
  user:
    expire: <yyyy-MM-dd hh:mm:ss.xxxxxx>
    token: <token_string>

# Add a new connection
To add a new connection, follow these steps:
1. $ ./appdctl.py login
2. Input your controller full hostname, including protocol and port
   i.e.: https://demo1.appdynamics.com:443
3. Input the API Client user name
4. Input the API Client user password
This will add a new pair of context and user in the **appdconfig.yaml** file, and will set it as the current-context.

# Help

Basic Commands (Intermediate):
   login         Log in to a server
   get           Display one or many resources

Advanced Commands:
   patch         Update field(s) of a resource using strategic merge patch

Usage:
   appdctl.py [flags] [options]
