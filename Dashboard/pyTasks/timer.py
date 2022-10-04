import Dashboard
from Dashboard import time, os
import datetime
from Dashboard.service import readJsonValueFromKey, MODE, MODE_PROCESS_IS_RUNNING
stop_threads = False


def timer_start():
    global stop_threads
    stop_threads = False
    userPrivateProfile = Dashboard.service.HOME_PATH + "DashboardSettings.json"  # /home/kiosk/DashboardSettings.json
    # filePath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_settings')) + "/public_settings.json"
    user_time = readJsonValueFromKey("USER_TIMER", userPrivateProfile)
    total_seconds = float(user_time) * 60

    while total_seconds > 0:
        if stop_threads:
            break
        timer = datetime.timedelta(seconds=total_seconds)
        print(timer)
        time.sleep(1)
        total_seconds -= 1
    if not stop_threads:
        while MODE_PROCESS_IS_RUNNING:
            time.sleep(0.02)
        MODE("OFF")
    print("Timer Stop")
