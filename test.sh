#/bin/bash

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

### Required packages: python python-requests python-libxml2

for XML_ENTITY in 	healthrules \
					transactiondetection-custom; do
	echo "### Get $XML_ENTITY ###"
	unzip -p tests.zip $XML_ENTITY.xml | $SCRIPTPATH/exportCSV.py get -f -
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
	unzip -p tests.zip $JSON_ENTITY.json | $SCRIPTPATH/exportCSV.py get -f -
#	read -p "Press any key" input
#	clear
done

#./appdctl.py get applications
#./appdctl.py get policies -a hipoteca-portal
#./appdctl.py get policies -a FullOnline,hipoteca-api-aks,hipoteca-portal
#./appdctl.py get schedules -a FullOnline,hipoteca-api-aks,hipoteca-portal
#./appdctl.py get health-rules -a FullOnline,hipoteca-api-aks,hipoteca-portal
#./appdctl.py get actions -a FullOnline,hipoteca-api-aks,hipoteca-portal
#./appdctl.py get detection-rules -a FullOnline,hipoteca-api-aks,hipoteca-portal
#./appdctl.py get businesstransactions -a FullOnline
#./appdctl.py get backends -a FullOnline
#./appdctl.py get healthrule-violations -a FullOnline --since=1d12h
#./appdctl.py get snapshots -a FullOnline --since=1d12h
#./appdctl.py get allothertraffic -a FullOnline --since=1d12h
#./appdctl.py patch schedules -a sandbox -p '{"timezone":"Europe\/Belgrade"}'
#./appdctl.py patch schedules -a sandbox -p '{"timezone":"Europe\/Brussels"}'