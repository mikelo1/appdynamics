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
###########################################

if [ $# -ne 3 ]; then 
    echo "Syntax: $0 <credentials_yaml_file> <environment> <application>"
	exit
fi

CRED_FILE=$1
ENVIRONMENT=$2
APPLICATION=$3

USER=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F"[:@]" '{print $2}' | sed 's/\s//g'`
ACCOUNT=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F"[:@]" '{print $3}' | sed 's/\s//g'`
PASS=`grep $ENVIRONMENT -A6 $CRED_FILE | grep password | awk -F: '{print $2}' | sed 's/\s//g'`
HOST=`grep $ENVIRONMENT -A6 $CRED_FILE | grep url | awk -F: '{print $3}' | sed 's/\///g'`

get_App_ID() {
	App_List=$(curl -s --user "${USER}@${ACCOUNT}:${PASS}" https://${HOST}/controller/rest/applications/)
	if [ $? -ne 0 ]; then
		echo "Something went wrong with the cURL command. Exiting..."
		exit
	fi
	App_Info=$(echo "${App_List}" | grep "<name>$APPLICATION</name>" -B1 -A1)
	if [ $? -ne 0 ]; then
		echo "Application $APPLICATION not found for account $ACCOUNT. Exiting..."
		exit
	fi
	echo "${App_Info}" | grep "id" | awk -F"[<>]" '{print $3}'
}

#APP_ID=$(get_App_ID)

if [ ! -d $APPLICATION ]; then mkdir $APPLICATION; fi

#REQUEST SNAPSHOTS
#curl -s --user "${USER}@${ACCOUNT}:${PASS}" "https://$HOST/controller/rest/applications/$APP_ID/request-snapshots?time-range-type=BEFORE_NOW&duration-in-mins=160&maximum-results=5000&output=JSON" -o $APPLICATION/request-snapshots.json
#curl -s --user "${USER}@${ACCOUNT}:${PASS}" "https://$HOST/controller/rest/applications/$APP_ID/request-snapshots?time-range-type=BEFORE_NOW&duration-in-mins=1440&maximum-results=5000&application-component-ids=${Tier_ID}&output=JSON" -o $APPLICATION/request-snapshots-${Tier_ID}.json

#HEALTH-RULE-VIOLATIONS
#curl -s --user "${USER}@${ACCOUNT}:${PASS}" "https://$HOST/controller/rest/applications/$APP_ID/problems/healthrule-violations?time-range-type=AFTER_TIME&duration-in-mins=1440&start-time=1572515956000" -o $APPLICATION/healthrule-violations.xml

#sleep 30s
echo "Start export application $3 from host $HOST with user $USER@$ACCOUNT"

for FILE in healthrules.xml actions.json policies.json; do
	ENTITY=`echo $FILE | awk -F. '{print $1}'`
	EXT=`echo $FILE | awk -F. '{print $2}'`
#	echo "Fetching $FILE..."
	curl -s --user "${USER}@${ACCOUNT}:${PASS}" https://$HOST/controller/$ENTITY/$APPLICATION -o $APPLICATION/$FILE
	if [ $? -ne 0 ]; then
		echo "Something went wrong with the cURL command. Exiting..."
	else
		echo -e "$ENTITY from $ACCOUNT downloaded to file ${APPLICATION}/${GREEN}${FILE}${NC}"
	fi
done

for FILE in transactiondetection-auto.xml transactiondetection-custom.xml; do
	ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
	TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
	EXT=`echo $FILE | awk -F[.-] '{print $3}'`
#	echo "Fetching $FILE..."
	curl -s --user "${USER}@${ACCOUNT}:${PASS}" https://$HOST/controller/$ENTITY/$APPLICATION/$TYPE -o $APPLICATION/$FILE
	if [ $? -ne 0 ]; then
		echo "Something went wrong with the cURL command. Exiting..."
	else
		echo -e "$ENTITY from $ACCOUNT downloaded to file ${APPLICATION}/${GREEN}${FILE}${NC}"
	fi
done