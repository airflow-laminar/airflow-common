command = "sudo journalctl --vacuum-time=2d"
"""
echo 'sudo systemctl stop airflow-celery-worker' | at now + 1 minute
echo 'sudo systemctl stop log2ram' | at now + 1 minute
echo 'sudo reboot now' | at now + 2 minutes
"""

"""
echo 'sudo systemctl stop airflow-celery-worker' | at now + 1 minute
echo 'sudo reboot now' | at now + 2 minutes
"""

"""
echo 'sudo lunchy stop timkpaine.airflow-celery-worker' | at now + 1 minute
echo 'sudo reboot now' | at now + 2 minutes
"""

"""
echo 'sudo systemctl stop airflow-webserver' | at now + 5 minute
echo 'sudo systemctl stop airflow-scheduler' | at now + 5 minute
echo 'sudo systemctl stop airflow-triggerer' | at now + 5 minute
echo 'sudo systemctl stop airflow-celery-flower' | at now + 5 minute
echo 'sudo systemctl stop airflow-celery-worker' | at now + 5 minute
echo 'sudo systemctl stop airflow-posgresql' | at now + 5 minute
echo 'sudo systemctl stop redis' | at now + 5 minute
echo 'sudo reboot now' | at now + 6 minutes
"""
