#!/usr/bin/env bash

echo -e "\e[33m WARNING: This script shows possible errors but will still pass regardless\e[0m"

# Just show warnings but allow commits to go through
ament_cpplint \
    --linelength=100 \
    --filter=-whitespace/newline,-whitespace/comments,-whitespace/line_length

exit 0
