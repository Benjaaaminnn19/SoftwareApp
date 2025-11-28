#!/bin/bash
# Script de post-deploy para Railway
cd SoftwareApp
python manage.py migrate --noinput
