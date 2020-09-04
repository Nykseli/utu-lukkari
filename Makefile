
INSTALLATION_PATH := /usr/bin/utu-lukkari

all:
	@ printf "Usage:\n\tmake install\n\tmake uninstall\n"

install:
	@ install -m 755 utu-lukkari.py $(INSTALLATION_PATH)
	@ echo "utu-lukkari installed succesfully"

uninstall:
	@ rm $(INSTALLATION_PATH)
	@ echo "utu-lukkari uninstalled succesfully"
