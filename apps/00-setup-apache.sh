# https://phoenixnap.com/kb/how-to-install-apache-web-server-on-ubuntu-18-04

# Update the package manager
sudo apt-get update

# Install Apache
sudo apt-get install apache2

# To stop Apache
sudo systemctl stop apache2.service

# To start Apache
sudo systemctl start apache2.service

# To restart Apache
sudo systemctl restart apache2.service

# To reload Apache
sudo systemctl reload apache2.service

# Change the write permissions
sudo chmod -R 777 /var/www/html/

# you can edit the HTML contents in this directory
# /var/www/html