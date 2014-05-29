# Install security auditing
sudo apt-get -y install acct
# See http://www.pointsoftware.ch/howto-bash-audit-command-logger/

# For Mac Mini install Wifi drivers
sudo apt-get update
sudo apt-get -y install linux-headers-generic linux-headers-`uname -r`
sudo apt-get -y install dpkg-dev debhelper dh-modaliases
sudo apt-get -y install --reinstall bcmwl-kernel-source
echo "blacklist bcm43xx\nblacklist b43\nblacklist bcma" | sudo tee -a /etc/modprobe.d/blacklist.conf

# Install SSH
sudo apt-get -y install openssh-server
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.original
sudo chmod a-w /etc/ssh/sshd_config.original
sudo /etc/init.d/ssh restart

# Install MySql
sudo apt-get -y install mysql-server
sudo netstat -tap | grep mysql
sudo service mysql restart

# Install Django
sudo apt-get -y install python-pip
sudo pip install uwsgi
sudo pip install django django-mptt django-reversion django-social_auth django-genericadmin

