#!/bin/bash
OLDIFS=$IFS
API_KEY=<YOUR_API_KEY>
IFS=,
i=1
[ ! -f $1 ] && { echo "$1 file not found"; exit -1; }
while read contact_id rest_of_shit
do
  test $i -eq 1 && ((i=i+1)) && continue
  contact_id=${contact_id%$'\r'}
  echo "Contact ID: $contact_id"
  curl -XDELETE "https://app.close.io/api/v1/contact/$contact_id/" -u $API_KEY:
done < $1
IFS=$OLDIFS
