#/bin/bash

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

### Required packages: python python-requests python-libxml2

for XML_ENTITY in healthrules transactiondetection; do
	echo "### ExportCSV $XML_ENTITY"
	$SCRIPTPATH/exportCSV.py $XML_ENTITY -i test.xml
done

for JSON_ENTITY in business-transactions backends actions policies; do
	echo "### ExportCSV $JSON_ENTITY"
	$SCRIPTPATH/exportCSV.py $JSON_ENTITY -i test.json
done

#./appdctl.py get applications
#./appdctl.py get policies -a hipoteca-portal
#./appdctl.py get policies -a FullOnline,hipoteca-api-aks,hipoteca-portal
#./appdctl.py get schedules -a FullOnline,hipoteca-api-aks,hipoteca-portal
#./appdctl.py patch schedules -a sandbox -p '{"timezone":"Europe\/Brussels"}'