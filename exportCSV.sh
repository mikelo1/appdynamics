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

USER=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F: '{print $2}' | sed 's/\s//g'`
PASS=`grep $ENVIRONMENT -A6 $CRED_FILE | grep password | awk -F: '{print $2}' | sed 's/\s//g'`
HOST=`grep $ENVIRONMENT -A6 $CRED_FILE | grep url | awk -F: '{print $3}' | sed 's/\///g'`
APP_ID=`grep $ENVIRONMENT -A6 $CRED_FILE | grep appID | awk -F: '{print $2}' | sed 's/\s//g'`
APP_NAME=`grep $ENVIRONMENT -A6 $CRED_FILE | grep appName | awk -F: '{print $2}' | sed 's/\s//g'`

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

### Required packages: python python-requests python-libxml2

if [ ! -d $APP_NAME ]; then mkdir $APP_NAME; fi


for FILE in healthrules.xml actions.json policies.json; do
	ENTITY=`echo $FILE | awk -F. '{print $1}'`
	EXT=`echo $FILE | awk -F. '{print $2}'`
	if [ ! -f $APP_NAME/$FILE ]; then
		echo "Fetching $FILE..."
		curl -s --user $USER:$PASS https://$HOST/controller/$ENTITY/$APP_ID -o $APP_NAME/$FILE -k
	fi
	echo "Converting file $FILE to CSV..."
	$SCRIPTPATH/exportCSV.py $ENTITY -i $APP_NAME/$FILE -o $APP_NAME/$ENTITY.csv
	#echo "Fetch data and translating to CSV..."
	#$SCRIPTPATH/exportCSV.py $ENTITY -s -p 443 -o $APP_NAME/$ENTITY.csv -H ${HOST}.saas.appdynamics.com -u ${USER} -p ${PASS} -a ${APP_ID} 
done

for FILE in business-transactions.json backends.json; do
	ENTITY=`echo $FILE | awk -F. '{print $1}'`
	EXT=`echo $FILE | awk -F. '{print $2}'`
	if [ ! -f $APP_NAME/$FILE ]; then
		echo "Fetching $FILE..."
		curl -s --user $USER:$PASS "https://$HOST/controller/rest/applications/$APP_ID/$ENTITY?output=JSON" -o $APP_NAME/$FILE -k
	fi
	echo "Converting file $FILE to CSV..."
	$SCRIPTPATH/exportCSV.py $ENTITY -i $APP_NAME/$FILE -o $APP_NAME/$ENTITY.csv
	#echo "Fetch data and translating to CSV..."
	#$SCRIPTPATH/exportCSV.py $ENTITY -s -p 443 -o $APP_NAME/$ENTITY.csv -H ${HOST}.saas.appdynamics.com -u ${USER} -p ${PASS} -a ${APP_ID} 
done

for FILE in transactiondetection-auto.xml transactiondetection-custom.xml; do
	ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
	TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
	EXT=`echo $FILE | awk -F[.-] '{print $3}'`
	
	if [ ! -f $APP_NAME/$FILE ]; then
		echo "Fetching $FILE..."
		curl -s --user $USER:$PASS https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -o $APP_NAME/$FILE -k
	fi
	echo "Converting file $FILE to CSV..."
	$SCRIPTPATH/exportCSV.py $ENTITY -i $APP_NAME/$FILE -o $APP_NAME/$ENTITY-$TYPE.csv
	#echo "Fetch data and translating to CSV..."
	#$SCRIPTPATH/exportCSV.py $ENTITY -s -p 443 -o $APP_NAME/$ENTITY.csv -H ${HOST}.saas.appdynamics.com -u ${USER} -p ${PASS} -a ${APP_ID} 
done