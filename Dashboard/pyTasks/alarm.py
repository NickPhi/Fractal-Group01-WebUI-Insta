import Dashboard.service
from Dashboard import datetime, time, re
from Dashboard.service import readJsonValueFromKey, MODE, power_supply_amp_, Signal_Generator_Controller

stop_threads = False


def isValidTime(time):
    regex = "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    p = re.compile(regex)
    if time == "":
        return False
    m = re.search(p, time)

    if m is None:
        return False
    else:
        return True


def check(text):
    print(text)
    pattern = r"^(1[0-2]|0?[1-9]):([0-5]?[0-9])(\s?[AP]M)?$ "
    result = re.search(pattern, text)
    return result != None


def alarm_start():
    userPrivateProfile = Dashboard.service.HOME_PATH + "DashboardSettings.json"  # /home/kiosk/DashboardSettings.json
    # userPrivateProfile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_settings')) + "/private_settings.json"
    user_time = readJsonValueFromKey("USER_ALARM", userPrivateProfile)

    in_time = datetime.strptime(user_time, "%I:%M %p")
    user_time = datetime.strftime(in_time, "%H:%M")

    #  check for correct format
    if isValidTime(user_time):
        print(user_time)
        t = time.strptime(user_time, "%H:%M")
        print(t)
        alarm_time = time.strftime("%I:%M:%S %p", t)
        print("Setting alarm for " + alarm_time)
    else:
        print("ELSE")
        alarm_time = '10:10:10 AM'
        print("Setting alarm for " + alarm_time)

    alarm_hour = alarm_time[0:2]
    alarm_min = alarm_time[3:5]
    alarm_sec = alarm_time[6:8]
    alarm_period = alarm_time[9:].upper()
    print(datetime.now())
    while True:
        if stop_threads:
            break
        now = datetime.now()

        current_hour = now.strftime("%I")
        current_min = now.strftime("%M")
        current_sec = now.strftime("%S")
        current_period = now.strftime("%p")

        if alarm_period == current_period:
            if alarm_hour == current_hour:
                if alarm_min == current_min:
                    if alarm_sec == current_sec:
                        power_supply_amp_("ON")
                        Signal_Generator_Controller("MHS_POWER_ON")
                        time.sleep(30)  # should ping devices to confirm
                        Dashboard.service.MODE_PROCESS_IS_RUNNING = False
                        MODE("ON")  # for how long
                        time.sleep(float(readJsonValueFromKey("USER_TIMER", userPrivateProfile)) * 60)
                        MODE("OFF")
                        break
    print("Alarm stop")


def convert24(str1):
    # Checking if last two elements of time
    # is AM and first two elements are 12
    if str1[-2:] == "AM" and str1[:2] == "12":
        return "00" + str1[2:-2]

    # remove the AM
    elif str1[-2:] == "AM":
        return str1[:-2]

    # Checking if last two elements of time
    # is PM and first two elements are 12
    elif str1[-2:] == "PM" and str1[:2] == "12":
        return str1[:-2]

    else:

        # add 12 to hours and remove PM
        return str(int(str1[:2]) + 12) + str1[2:8]
