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

USER=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F: '{print $2}' | sed 's/\s//g'`
PASS=`grep $ENVIRONMENT -A6 $CRED_FILE | grep password | awk -F: '{print $2}' | sed 's/\s//g'`
APICLIENT=`grep $ENVIRONMENT -A6 $CRED_FILE | grep apiclient | awk -F: '{print $2}' | sed 's/\s//g'`
APISECRET=`grep $ENVIRONMENT -A6 $CRED_FILE | grep apisecret | awk -F: '{print $2}' | sed 's/\s//g'`
HOST=`grep $ENVIRONMENT -A6 $CRED_FILE | grep url | awk -F: '{print $3}' | sed 's/\///g'`

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

### Required packages: python python-requests python-libxml2

if [ ! -d $APPLICATION ]; then mkdir $APPLICATION; fi

for FILE in healthrules.xml actions.json policies.json; do
	ENTITY=`echo $FILE | awk -F. '{print $1}'`
	EXT=`echo $FILE | awk -F. '{print $2}'`
#	if [ ! -f $APPLICATION/$FILE ]; then
#		echo "Fetching $FILE..."
#		curl -s --user $USER:$PASS https://$HOST/controller/$ENTITY/$APP_ID -o $APPLICATION/$FILE -k
#	fi
#	echo "Converting file $FILE to CSV..."
#	$SCRIPTPATH/exportCSV.py $ENTITY -i $APPLICATION/$FILE -o $APPLICATION/$ENTITY.csv
	echo "Fetch data and translating to CSV..."
	$SCRIPTPATH/exportCSV.py $ENTITY -s -P 443 -o $APPLICATION/$ENTITY.csv -H ${HOST} -u ${USER} -p ${PASS} -a ${APPLICATION}
done

for FILE in business-transactions.json backends.json; do
	ENTITY=`echo $FILE | awk -F. '{print $1}'`
	EXT=`echo $FILE | awk -F. '{print $2}'`
#	if [ ! -f $APPLICATION/$FILE ]; then
#		echo "Fetching $FILE..."
#		curl -s --user $USER:$PASS "https://$HOST/controller/rest/applications/$APP_ID/$ENTITY?output=JSON" -o $APPLICATION/$FILE -k
#	fi
#	echo "Converting file $FILE to CSV..."
#	$SCRIPTPATH/exportCSV.py $ENTITY -i $APPLICATION/$FILE -o $APPLICATION/$ENTITY.csv
	echo "Fetch data and translating to CSV..."
	$SCRIPTPATH/exportCSV.py $ENTITY -s -P 443 -o $APPLICATION/$ENTITY.csv -H ${HOST} -u ${USER} -p ${PASS} -a ${APPLICATION}
done

for FILE in transactiondetection-auto.xml transactiondetection-custom.xml; do
	ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
	TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
	EXT=`echo $FILE | awk -F[.-] '{print $3}'`
#	if [ ! -f $APPLICATION/$FILE ]; then
#		echo "Fetching $FILE..."
#		curl -s --user $USER:$PASS https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -o $APPLICATION/$FILE -k
#	fi
#	echo "Converting file $FILE to CSV..."
#	$SCRIPTPATH/exportCSV.py $ENTITY -i $APPLICATION/$FILE -o $APPLICATION/$ENTITY-$TYPE.csv
	echo "Fetch data and translating to CSV..."
	$SCRIPTPATH/exportCSV.py $ENTITY -s -P 443 -o $APPLICATION/$ENTITY.csv -H ${HOST} -u ${USER} -p ${PASS} -a ${APPLICATION}
done

ALLOTHERTRAFFIC_LIST=$(curl -s --user $USER:$PASS "https://$HOST/controller/rest/applications/$APP_ID/business-transactions?output=JSON" | grep "_APPDYNAMICS_DEFAULT_TX_" -A2 | grep "id" | awk -F[:,] '{print $2}')
for BT_ID in ${ALLOTHERTRAFFIC_LIST}; do
	FILE=allothertraffic-${BT_ID}.json
#	if [ ! -f $APPLICATION/$FILE ]; then
#		echo "Fetching $FILE..."
#		curl -s --user $USER:$PASS "https://$HOST/controller/rest/applications/$APP_ID/request-snapshots/?business-transaction-ids=$BT_ID&time-range-type=BEFORE_NOW&duration-in-mins=1440&output=JSON" -o $APPLICATION/$FILE -k
#	fi
#	echo "Converting file $FILE to CSV..."
#	$SCRIPTPATH/exportCSV.py allothertraffic -i $APPLICATION/$FILE -o $APPLICATION/allothertraffic-${BT_ID}.csv
	echo "Fetch data and translating to CSV..."
	$SCRIPTPATH/exportCSV.py allothertraffic -s -P 443 -o $APPLICATION/$FILE.csv -H ${HOST} -u ${USER} -p ${PASS} -a ${APPLICATION}
done

$SCRIPTPATH/exportCSV.py events -s -P 443 -o $APPLICATION/events.csv -H ${HOST} -u ${USER} -p ${PASS} -a ${APPLICATION}
#$SCRIPTPATH/exportCSV.py applications -s -P 443 -o applications.csv -H ${HOST} -u ${USER} -p ${PASS}
#$SCRIPTPATH/exportCSV.py dashboards -s -P 443 -o $APPLICATION/dashboards.csv -H ${HOST} -u ${USER} -p ${PASS} --api-client-name ${APICLIENT} --api-client-secret ${APISECRET}