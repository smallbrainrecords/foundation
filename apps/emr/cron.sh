#!/bin/bash
cd /var/www/andromeda/foundation
source /home/softdevelop_vd/Env/foundation/bin/activate

echo "----------------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
echo "Start of cron jobs for this run on: $(date)" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
echo "----------------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log

python manage.py cron review_colorectal_cancer_risk_assessment &>> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "---------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
python manage.py cron patient_needs_a_plan_for_colorectal_cancer_screening &>> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "---------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
python manage.py cron a1c_order_was_automatically_generated &>> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "---------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
python manage.py cron physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times &>> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "---------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
python manage.py cron physician_adds_the_same_medication_to_the_same_problem_concept_id_more_than_3_times &>> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "---------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
python manage.py cron problem_relationship_auto_pinning_for_3_times_matched &>> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "---------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
  echo "" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log

echo "--------------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
echo "End of cron jobs for this run on: $(date)" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
echo "--------------------------------------------------------------" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log
echo "" >> /var/www/andromeda/cronlogs/smallbrain-cronjob.log

deactivate
