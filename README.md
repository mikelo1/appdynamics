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

# Examples:
Basic Commands (Basic):
 * Get applications list
   $ appdctl.py get applications
 * Get policies list for specific applications
   $ appdctl.py get policies -a myApp1,myApp2
 * Get schedules for specific application
   $ appdctl.py get schedules -a myApp1
 * Get health rules for specific application
   $ appdctl.py get health-rules -a myApp1
 * Get actions for specific application
   $ appdctl.py get actions -a myApp1
 * Get transaction detection rules for specific application
   $ appdctl.py get detection-rules -a myApp1
 * Get business transactions for specific application
   $ appdctl.py get businesstransactions -a myApp1
 * Get backends for specific application
   $ appdctl.py get backends -a myApp1

Advanced Commands:
 * Get health rule violations for specific application and last 1 day and a half
   $ appdctl.py get healthrule-violations -a myApp1 --since=1d12h
 * Get last 1 day snapshots for specific application, where user experience was ERROR and business transaction ID is 12345
   $ appdctl.py get snapshots -a myApp1 -l user-experience=ERROR,business-transaction-ids=12345 --since=1d -o JSON
 * Update timezone for all schedules of a specific application
   $ appdctl.py patch schedules -a myApp1 -p '{"timezone":"Europe\/Belgrade"}'