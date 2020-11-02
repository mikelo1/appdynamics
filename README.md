# AppDynamics control tool

AppDCTL is aimed to control and maintain an AppDynamics controller configuration.
In order to establish a connection to an AppDynamics controller, please login first.


# Required packages

	python python-requests python-libxml2



# Authentication to the AppDynamics API

AppDCTL is using [API Clients](https://docs.appdynamics.com/display/PRO45/API+Clients) to authenticate to the AppDynamics API.

First time authentication needs to be done through the **login** command, which will create a new context in the **appdconfig.yaml** file. The login command can be used to create a new context or to change the current context to another existing one.

One context will include an username, a servername and an authentication token -which duration is defined in the AppDynamics API Client user. During the validity of the token, the user will be able to run any commands without having to input any credentials. Once the token has expired, API Client password will be requested.

## Login to a controller context
Login can be done with manual keyboard input or with a basic authentication file in CSV format
Either way, if the context doesn't exist in the **appdconfig.yaml** file, it will create a new entry and set it as the current-context.

To login with a manual input of the credentials, follow these steps:
1. $ ./appdctl.py login
2. Input your controller full hostname, including protocol and port
   i.e.: https://demo1.appdynamics.com:443
3. Input the API Client user name
4. Input the API Client user password

In case of having a basic authentication file, follow this syntax:
1. $ ./appdctl.py login --api-client <my_APIClient_username>@<my_account_name1> --basic-auth-file <path_to_auth_file>

## appdconfig.yaml file format

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

## basicAuth file format
<password1>,<my_APIClient_username1>@<my_account_name1>
<password2>,<my_APIClient_username2>@<my_account_name2>



# Help

Basic Commands (Intermediate):
   login         Log in to a server
   get           Display one or many resources

Advanced Commands:
   patch         Update field(s) of a resource using strategic merge patch
   update        Update status of a resource

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