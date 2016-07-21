#!/bin/bash


while :
do
  python -m bi_etl.scheduler.scheduler 
  echo "restarting in 30 seconds"
  sleep 30
done

