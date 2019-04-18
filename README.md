# sensorimotordb
SensoriMotorDatabase

Requirements
- Python 2.7
- mysql-server
- R
- run pip install -r requirements.txt

Installation
- Create database uscbp_sensorimotordb
- Copy uscbp/settings.py.default to uscpbp/settings.py
- Update admin, database info, media root, static root, template dirs
- Run python manage.py syncdb
- Configure elasticsearch
