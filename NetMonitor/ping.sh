#!/bin/sh

#PING SHELL SCRIPT
#DESTINATION IP/HOST AS PARAMETER (i.e. ./ping.sh 8.8.8.8 )
#RETURNS AVG MS LATENCY IF PING OK
#ELSE RETURNS 0 AND ERROR CODE

DESTINATION=$1
NPINGS=1
TIMEOUT=1

OUTPUT="$(timeout $TIMEOUT ping -c $NPINGS $DESTINATION | sed '$!d;s|.*/\([0-9.]*\)/.*|\1|')"

if [ "$OUTPUT" = "" ]
then
	echo 0
	exit 1
fi

echo $OUTPUT | grep -Eq '^[-+]?([0-9]*\.[0-9]+|[0-9]+\.[0-9]*)$' && echo $OUTPUT && exit 0

echo 0
exit 1
