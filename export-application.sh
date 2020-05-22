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
	echo "${App_Info}" | grep "<id>" | awk -F"[<>]" '{print $3}'
}


if [ ! -d $APPLICATION ]; then mkdir $APPLICATION; fi

echo "Start export application $3 from host $HOST with user $USER@$ACCOUNT"

#for FILE in healthrules.xml actions.json policies.json; do
#	ENTITY=`echo $FILE | awk -F. '{print $1}'`
#	EXT=`echo $FILE | awk -F. '{print $2}'`
#	curl -s --user "${USER}@${ACCOUNT}:${PASS}" https://$HOST/controller/$ENTITY/$APPLICATION -o $APPLICATION/$FILE
#done

APP_ID=$(get_App_ID)

for ENTITY in health-rules actions policies schedules; do
#	echo "Fetching $ENTITY for application $APPLICATION($APP_ID)..."
	curl -s --user "${USER}@${ACCOUNT}:${PASS}" https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY -o $APPLICATION/$ENTITY.json
	if [ $? -ne 0 ]; then
		echo "Something went wrong with the cURL command. Exiting..."
	else
		echo -e "$ENTITY from $ACCOUNT downloaded to file ${APPLICATION}/${GREEN}${ENTITY}.json${NC}"
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

