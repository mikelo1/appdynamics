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
# unzip -p tests.zip dashboards.json | ./appdctl.py get dashboards -f -
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

#./appdctl.py get -f EVO.SaaS.UAT/sandbox/policies.json
#./appdctl.py get -f EVO.SaaS.UAT/FullOnline/policies.json
#./appdctl.py get -f EVO.SaaS.UAT/sandbox/actions.json
#./appdctl.py get -f EVO.SaaS.UAT/FullOnline/actions.json