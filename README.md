EducnetExtractor is a program for automatic extraction and compilation of ENPC student C++ duties, with a automatic cmake generator.

# Installation

```shell
sudo apt install git python3-pip patool p7zip rar unrar
pip3 install pyunpack
git clone https://github.com/belosthomas/EducnetExtractor.git
cd EducnetExtractor
chmod +x EducnetExtractor.py
mkdir -p /usr/local
mkdir -p /usr/local/bin
sudo cp EducnetExtractor.py /usr/local/bin/correction
```

# Execution

```
correction -z zipfile.zip -d . -e true
```

**-z** : The zip file to extract
**-d** : Where to extract the zip file
**-e** : Execute the compiled program
