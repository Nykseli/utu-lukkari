#!/bin/sh

###
# Script for installing utu-lukkari in termux
# Usage:
# ./termux_install.sh [option]
# Options:
#   install     install the program [default]
#   update      fetch the latest changes and install
#   uninstall   remove installed executable
##

set -e

install() {
    CPWD=`pwd`
    cd ~
    cp "$CPWD/utu-lukkari.py" ../usr/bin/utu-lukkari
    cd $CPWD
    echo "utu-lukkari installed succesfully"
    exit 0
}

update() {
    git pull
    install
}

uninstall() {
    CPWD=`pwd`
    cd ~
    rm ../usr/bin/utu-lukkari
    cd $CPWD
    exit 0
}

if [ -z $1 ]
then
    # Install by default if there is no option selected
    install
fi


# check the option
case "$1" in
    "update")
        update
        ;;
    "install")
        install
        ;;
    "uninstall")
        uninstall
        ;;
    *)
        echo "Invalid option: $1"
        exit 1
esac
