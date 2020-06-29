#/bin/bash

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

### Required packages: python python-requests python-libxml2

for XML_ENTITY in 	healthrules \
					transactiondetection-custom; do
	echo "### Get $XML_ENTITY ###"
	unzip -p tests.zip $XML_ENTITY.xml | $SCRIPTPATH/appdctl.py get -f -
#	read -p "Press any key" input
#	clear
done

for JSON_ENTITY in 	actions \
					actions-legacy  \
					allothertraffic \
					applications \
					backends \
					business-transactions \
					dashboards \
					health-rules \
					healthrule-violations \
					policies \
					policies-legacy \
					request-snapshots \
					schedules ; do
	echo "### Get $JSON_ENTITY ###"
	unzip -p tests.zip $JSON_ENTITY.json | $SCRIPTPATH/appdctl.py get -f -
#	read -p "Press any key" input
#	clear
done

for JSON_ENTITY in 	healthrule-violations \
					request-snapshots ; do
	echo "### Get $JSON_ENTITY ###"
	unzip -p tests.zip $JSON_ENTITY.json | $SCRIPTPATH/appdctl.py get -f - -o JSON
#	read -p "Press any key" input
#	clear
done