#!/bin/bash
#!/home/gisteam/anaconda3/bin/python
source /home/gisteam/demo-alerts/.env
source /home/gisteam/.bashrc
echo prepping alerts
/home/gisteam/anaconda3/bin/python /home/gisteam/demo-alerts/send_alerts.py
echo sent alerts