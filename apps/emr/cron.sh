#!/bin/bash

# path to log file to log execution history and command output, if any (see apps/emr/cron.py for print() output generated in each cron job)  
LOG_FILE="/var/www/andromeda/cronlogs/smallbrain-cronjob.log"

# cd to project directory
cd /var/www/andromeda/smallbrain2/foundation

# activate virtualenv
source /var/www/andromeda/smallbrain2/env.smallbrain2/bin/activate

# using echo to add lines & characters to make log file easier to read 

echo "----------------------------------------------------------------" >> $LOG_FILE
echo "Start of cron jobs for this run on: $(date)" >> $LOG_FILE
echo "----------------------------------------------------------------" >> $LOG_FILE

# TODO: review/revise both colon cancer execution plans; keep deactivated for now 
#
# python manage.py cron review_colorectal_cancer_risk_assessment &>> $LOG_FILE
#   echo "---------------------------------------------------------" >> $LOG_FILE
#   echo "" >> $LOG_FILE
#
# python manage.py cron patient_needs_a_plan_for_colorectal_cancer_screening &>> $LOG_FILE
#   echo "---------------------------------------------------------" >> $LOG_FILE
#   echo "" >> $LOG_FILE

python manage.py cron a1c_order_was_automatically_generated &>> $LOG_FILE
  echo "---------------------------------------------------------" >> $LOG_FILE
  echo "" >> $LOG_FILE

python manage.py cron physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times &>> $LOG_FILE
  echo "---------------------------------------------------------" >> $LOG_FILE
  echo "" >> $LOG_FILE

python manage.py cron physician_adds_the_same_medication_to_the_same_problem_concept_id_more_than_3_times &>> $LOG_FILE
  echo "---------------------------------------------------------" >> $LOG_FILE
  echo "" >> $LOG_FILE

python manage.py cron problem_relationship_auto_pinning_for_3_times_matched &>> $LOG_FILE
  echo "---------------------------------------------------------" >> $LOG_FILE
  echo "" >> $LOG_FILE

echo "--------------------------------------------------------------" >> $LOG_FILE
echo "End of cron jobs for this run on: $(date)" >> $LOG_FILE
echo "--------------------------------------------------------------" >> $LOG_FILE
echo "" >> $LOG_FILE

# deactivate virtualenv at end of cron jobs
deactivate
