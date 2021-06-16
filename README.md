# AppDynamics control tool

AppDCTL is aimed to control and maintain an AppDynamics controller configuration.
In order to establish a connection to an AppDynamics controller, please login first.


# Required packages

	python python-requests python-libxml2 yaml



# Authentication to the AppDynamics API

AppDCTL is using [API Clients](https://docs.appdynamics.com/display/PRO45/API+Clients) to authenticate to the AppDynamics API.
Every new connection needs to request a new authentication token -which duration is defined in the AppDynamics API Client user.
During the validity of the token, the user will be able to run any commands without having to request a new token.
For a new token request, API Client credentials need to be provided.

## Controller contexts
With the controller contexts configuration it's possible to switch between appdynamics controllers.
Each context will include a servername, username and one associated token with the expiration date.

### appdconfig.yaml file format

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


# Help

Basic Commands (Intermediate):
   get           Display one or many resources

Advanced Commands:
   apply         Apply a configuration to a resource by filename or stdin
   patch         Update field(s) of a resource using strategic merge patch
   update        Update status of a resource

Other Commands:
  config        Modify appdconfig files

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
 * Get last 1 day snapshots for specific application, where error ID is 500
   $ appdctl.py get snapshots -a myApp1 -l error-ids=500 --since=1d -o JSON
 * Update timezone for all schedules of a specific application
   $ appdctl.py patch schedules -a myApp1 -p '{"timezone":"Europe\/Belgrade"}'
