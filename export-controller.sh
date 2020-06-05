#/bin/bash

###########################################
### Read credentials from YAML file     ###
###########################################
### Script will read from a YAML file   ###
### with the following format:          ###
### ----------------------------------- ###
### <environment>:                      ###
###     secret:                         ###
###         username: <user>@<account>  ###
###         password: <password>        ###
###         apiclient: <apiClient_name> ###
###         apisecret: <client_secret>  ###
###         url: <base_controller_url>  ###
###         appID: <application_ID>     ###
###         appName: <application_name> ###
###########################################

if [ $# -ne 2 ]; then 
    echo "Syntax: $0 <credentials_yaml_file> <environment>"
	exit
fi

CRED_FILE=$1
ENVIRONMENT=$2

USER=`grep $ENVIRONMENT -A8 $CRED_FILE | grep username | awk -F: '{print $2}' | sed 's/\s//g'`
PASS=`grep $ENVIRONMENT -A8 $CRED_FILE | grep password | awk -F: '{print $2}' | sed 's/\s//g'`
APICLIENT=`grep $ENVIRONMENT -A8 $CRED_FILE | grep apiclient | awk -F: '{print $2}' | sed 's/\s//g'`
APISECRET=`grep $ENVIRONMENT -A8 $CRED_FILE | grep apisecret | awk -F: '{print $2}' | sed 's/\s//g'`
HOST=`grep $ENVIRONMENT -A8 $CRED_FILE | grep url | awk -F: '{print $3}' | sed 's/\///g'`

GREEN='\033[0;32m'
NC='\033[0m' # No Color

if [ ! -d $ENVIRONMENT ]; then mkdir $ENVIRONMENT; fi

# https://docs.appdynamics.com/display/PRO45/API+Clients#APIClients-using-the-access-token
# https://docs.appdynamics.com/display/PRO45/API+Clients
echo_appd_access_token() {
	curl -s --user "$APICLIENT:$APISECRET" \
		    -X POST -H "Content-Type: application/vnd.appd.cntrl+protobuf;v=1" \
		    -d "grant_type=client_credentials&client_id=$APICLIENT&client_secret=$APISECRET" \
			"https://${HOST}/controller/api/oauth/access_token" | grep -o "\"access_token\": \"[^\"]*\"," | awk -F\" '{print $4}'
}

ACCESS_TOKEN=$(echo_appd_access_token)
if [ -z $ACCESS_TOKEN ]; then echo "Something went wrong with the access token. Exiting..." ; exit; fi

echo -ne "AppDynamics Controller version: "
curl -s -H "Authorization:Bearer $ACCESS_TOKEN" "https://${HOST}/controller/rest/configuration?name=schema.version&output=JSON" | grep value | awk '{print $2}' | sed -e 's/"//g'
if [ $? -ne 0 ]; then
	echo "Something went wrong with the cURL command. Exiting..." ; exit
fi

#APPLICATION_LIST
curl -s -H "Authorization:Bearer $ACCESS_TOKEN" "https://${HOST}/controller/rest/applications?output=JSON" -o ${ENVIRONMENT}/applications.json
if [ $? -ne 0 ]; then
	echo "Something went wrong with the cURL command. Exiting..." ; exit
else
	echo -e "$HOST application list downloaded to file ${GREEN}applications.json${NC}"
fi

#EMAIL TEMPLATES
curl -s -H "Authorization:Bearer $ACCESS_TOKEN" https://$HOST/controller/actiontemplate/email -o ${ENVIRONMENT}/emailTemplates.json
if [ $? -ne 0 ]; then
	echo "Something went wrong with the cURL command. Exiting..." ; exit
else
	echo -e "$HOST controller email templates downloaded to file ${GREEN}emailTemplates.xml${NC}"
fi

#CONFIGURATION
curl -s -H "Authorization:Bearer $ACCESS_TOKEN" "https://${HOST}/controller/rest/configuration?output=JSON" -o ${ENVIRONMENT}/config.json
if [ $? -ne 0 ]; then
	echo "Something went wrong with the cURL command. Exiting..."; exit
else
	echo -e "$HOST controller configuration downloaded to file ${GREEN}config.xml${NC}"
fi

#DASHBOARD_LIST
DASHBOARDS_BY_TYPE=`curl -s -H "Authorization:Bearer $ACCESS_TOKEN" \
 "https://${HOST}/controller/restui/dashboards/getAllDashboardsByType/false"`
if [ $? -ne 0 ]; then
	echo "Something went wrong with the cURL command. Exiting..."; exit
else
	echo $DASHBOARDS_BY_TYPE > ${ENVIRONMENT}/dashboards.json
	echo -e "Dashboard list from $ENVIRONMENT downloaded to file ${GREEN}dashboards.json${NC}"
fi
exit
#DASHBOARD_EXPORT_ALL
 if [ $? ] && [ DASHBOARDS_BY_TYPE != "Failed to authenticate: invalid access token." ]; then 
	DASHBOARD_LIST=`echo $DASHBOARDS_BY_TYPE | grep -o "\"id\" : [0-9]*," | sed -e 's/[id:",]//g'`
	for DASHBOARD_ID in $DASHBOARD_LIST; do
		curl -s -H "Authorization:Bearer $ACCESS_TOKEN" "https://${HOST}/controller/CustomDashboardImportExportServlet?dashboardId=$DASHBOARD_ID" -o ${ENVIRONMENT}/dashboard-${DASHBOARD_ID}-${HOST}.json
		if [ $? -ne 0 ]; then
			echo "Something went wrong with the cURL command. Exiting..."; exit
		else
			echo -e "Dashboard ${DASHBOARD_ID} from $ENVIRONMENT downloaded to file ${GREEN}dashboard-${DASHBOARD_ID}-${HOST}.json${NC}"
		fi
	done
else
	echo $DASHBOARDS_BY_TYPE
fi