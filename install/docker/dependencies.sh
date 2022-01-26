useradd -ms /bin/bash user
su user
cd /home

apt-get install wget -y
apt-get install unzip -y

# wget https://chromedriver.storage.googleapis.com/91.0.4472.101/chromedriver_linux64.zip
# for 92 https://chromedriver.storage.googleapis.com/92.0.4515.43/chromedriver_linux64.zip
# for 91 https://chromedriver.storage.googleapis.com/91.0.4472.101/chromedriver_linux64.zip
# unzip chromedriver_linux64.zip
su -
cd /home/shared-folder
chown user:user chromedriver
chmod +x chromedriver
# mv chromedriver /usr/bin

pip install --user -U nltk
pip install selenium spacy textblob
pip install google-api-python-client

cd QMOMI_tool/Codebase
# conda config --append channels conda-forge
conda install --file Requirements.txt
pip install -r Requirements.txt

apt-get update
apt-get install -y curl unzip xvfb libxi6 libgconf-2-4
# apt-get -y install xorg xvfb gtk2-engines-pixbuf
# apt-get -y install dbus-x11 xfonts-base xfonts-100dpi xfonts-75dpi xfonts-cyrillic xfonts-scalable
# wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# dpkg -i google-chrome-stable_current_amd64.deb
# apt-get install -f
apt-get install chromium-browser -y
