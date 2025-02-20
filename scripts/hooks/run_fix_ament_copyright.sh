#!/usr/bin/env bash

username="Analog Devices, Inc."

# To list all supported licenses, run the following command:
# ament_copyright --list-licenses
license=apache2

ament_copyright --add-missing "$username" "$license" "$@"
