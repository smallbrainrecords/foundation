#kill -9 $(pidof manage)
#kill -9 $(pidof python)
cd
rm -rf core
git clone https://github.com/smallbrainrecords/foundation.git
mv foundation core

cd core
#mkdir static && cd static && git clone https://github.com/smallbrainrecords/foundation.git

python manage.py syncdb
#sudo netstat -plnt
#echo $$
#sh /home/tim/core/runserver.sh &
#kill -9 $$
