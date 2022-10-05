from Dashboard import threading, time, pyTasks, os, requests, json, subprocess, jsonify, sys

#  GLOBALS
t1 = threading.Thread  # alarm thread
t2 = threading.Thread  # timer thread
timer_state = ""  # Global Variable
alarm_state = ""  # Global Variable
ON_start = 0
ON_end = 0
##### Load from Profile #####
HOME_PATH = ""  # Path to /home/kiosk
USER_NAME = ""
PATH_TO_POST_TO = ""  # None
WIFI_DRIVER_NAME = ""
MY_CURRENT_VERSION = 0
##### Download from web #####
ADMIN_EMAIL = ""
ADMIN_PHONE = ""
AUTHENTICATION = 0
COMMAND = ""
SIGLENT = 0
FORCE_UPDATE = 0
URL_FOR_UPDATE = ""
WEB_LATEST_UPDATE = 0
##### Extra variables #######
ONCE_INDEX = 0
POWER_GEN_STATE = 0
MODE_PROCESS_IS_RUNNING = False
MODE_STATE = ""
SiglentIP = ""
userPrivateProfile = ""
auth_key = 'klshdfgkjh(*&89y(*YF^*&%&RIUHEFIH986893yh4rjfskjdhffhgajkdfni&*%&^^IUJhknfga'
filePath_private_settings = os.path.dirname(os.path.abspath(__file__)) + "/_settings/private_settings.json"
filePath_public_settings = os.path.dirname(os.path.abspath(__file__)) + "/_settings/public_settings.json"


# GLOBALS

# if index is refreshed it may keep threads running may want to kill them unless index will never refresh

###########################################################################
############################ FIRST CHECK ##################################
###########################################################################


def start_index():
    global ONCE_INDEX, AUTHENTICATION, SIGLENT, PATH_TO_POST_TO
    if ONCE_INDEX == 0:  # have we done this once?
        load__profile()  # load all profile/global variables
        if wifi_check():  # WiFi Check
            Download_Profile()
            run_command()  # Only called once and from here.
            send_statistic('IP', str(getPublicIP()))  # Send IP Address - Web Server
            print("wifi pass")
            print("profile downloaded")
            print("IP obtained")
            if check_for_auth():  # comes first from the profile  # if profile says 0
                if update_check():  # if update do update stuff
                    return "Update"
                threading.Thread(target=authentication_thread).start()  # start authentication loop thread
                power_supply_amp_("ON")  # turn amp on when we authenticate
                if SIGLENT == 1:  # if siglent on then pass powering signal generator
                    pass  # cannot control Siglent Device Power state test
                    # Signal_Generator_Controller("SIGLENT_POWER_ON")
                else:
                    Signal_Generator_Controller("MHS_POWER_ON")  # turn on signal generator
                ONCE_INDEX = "1"  # remember we have already loaded all we need
                return "Authenticated"
            else:
                restart_15()  # reboot in 15 minutes
                return "Not-Authenticated"
                # It will cycle so best to turn itself off than restart
        else:
            return "no-Wifi"
    else:
        return "Load_Index"


###########################################################################
########################### HANDLES GPIO ##################################
###########################################################################


def MODE(mode):
    global SIGLENT, ON_start, ON_end, MODE_PROCESS_IS_RUNNING, MODE_STATE, SiglentIP
    if mode == "ON":
        if MODE_PROCESS_IS_RUNNING:  # does this eliminate the need for ajax
            return
        if MODE_STATE == "ON":
            return
        MODE_PROCESS_IS_RUNNING = True
        MODE_STATE = "ON"
        if SIGLENT == 1:  # if siglent on then pass siglent signal
            if SiglentIP is None:
                return
            Signal_Generator_Controller("SIGLENT_ON")
            # maybe want a confirmation this is working before proceeding
        else:
            Signal_Generator_Controller("MHS_ON")  # pass signal generator
        speaker_protection_("ON")
        ON_start = time.time()
        send_statistic('TOTAL_TIMES_USED', "1")
        MODE_PROCESS_IS_RUNNING = False
    elif mode == "OFF":
        if MODE_PROCESS_IS_RUNNING:
            return
        MODE_PROCESS_IS_RUNNING = True
        ON_end = time.time()
        run_time = float((ON_end - ON_start) / 60)
        send_statistic('MINUTES', run_time)
        print(run_time)
        speaker_protection_("OFF")
        if SIGLENT == 1:  # if siglent on then pass siglent signal off
            Signal_Generator_Controller("SIGLENT_OFF")
        else:
            Signal_Generator_Controller("MHS_OFF")  # pass signal generator off
        MODE_PROCESS_IS_RUNNING = False
        MODE_STATE = "OFF"


def power_supply_amp_(mode):
    # Relay HIGH is off LOW is on
    if mode == "ON":
        os.system('sudo gpioset 1 91=0')
    elif mode == "OFF":
        os.system('sudo gpioset 1 91=1')


def Signal_Generator_Controller(mode):
    global filePath_private_settings, POWER_GEN_STATE, HOME_PATH
    # Relay HIGH is off LOW is on
    if mode == "MHS_POWER_ON":
        os.system('sudo gpioset 1 92=0')
        POWER_GEN_STATE = "1"
    elif mode == "MHS_POWER_OFF":
        os.system('sudo gpioset 1 92=1')
        POWER_GEN_STATE = "0"
    elif mode == "MHS_ON":
        os.system(
            'sudo ' + HOME_PATH + 'MHS-5200-Driver/mhs5200 /dev/ttyUSB0 channel 1 arb 0 amplitude 4 freq 364 on')
        time.sleep(.4)
    elif mode == "MHS_OFF":
        os.system(
            'sudo ' + HOME_PATH + 'MHS-5200-Driver/mhs5200 /dev/ttyUSB0 channel 1 arb 0 amplitude 4 freq 364 off')
        time.sleep(.4)
    elif mode == "SIGLENT_ON":
        pyTasks.siglent.ON()
        # time.sleep(.4) has its own time out
    elif mode == "SIGLENT_OFF":
        pyTasks.siglent.OFF()
    elif mode == "SIGLENT_INVERT":
        while MODE_PROCESS_IS_RUNNING:
            time.sleep(0.02)
        MODE("OFF")
        pyTasks.siglent.INVERT()


def speaker_protection_(mode):
    # Relay HIGH is off LOW is on
    if mode == "ON":
        os.system('sudo gpioset 1 93=0')
    elif mode == "OFF":
        os.system('sudo gpioset 1 93=1')
        time.sleep(.05)


###########################################################################
#################### Few Other Functions ##################################
###########################################################################


def send_settings_on_settings_page(data):
    global timer_state, alarm_state, ON_start, ON_end, HOME_PATH, USER_NAME, PATH_TO_POST_TO, WIFI_DRIVER_NAME, \
        MY_CURRENT_VERSION, ADMIN_EMAIL, ADMIN_PHONE, AUTHENTICATION, COMMAND, SIGLENT, FORCE_UPDATE, \
        URL_FOR_UPDATE, WEB_LATEST_UPDATE, ONCE_INDEX, POWER_GEN_STATE, MODE_PROCESS_IS_RUNNING, MODE_STATE, auth_key, \
        SiglentIP
    try:
        if 'troubleshoot' in data:
            try:
                message = "    USER_NAME: " + str(USER_NAME) + "    WIFI_DRIVER_NAME: " + str(WIFI_DRIVER_NAME) + \
                          "    auth_key: " + str(auth_key)
                send_statistic('ACTIVE_UPDATE', message)
                test_string = "Path= what to send"
                # file size # sub process lsblk
                HDD_size = str(subprocess.check_output('lsblk', shell=True))
                # IP address
            except Exception as error:
                send_statistic('ACTIVE_UPDATE', 'settings_send failed: troubleshoot ' + 'troubleshoot' + str(error))
        if 'extra_Settings' in data:
            while MODE_PROCESS_IS_RUNNING:
                time.sleep(0.02)
            MODE("OFF")
        if 'rollback' in data:
            try:
                filePath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "/fix.py"
                os.system('python3 ' + filePath)  #
            except subprocess.CalledProcessError as err:
                send_statistic('ACTIVE_UPDATE', str(err))
        if 'email' in data:
            try:
                send_statistic('ACTIVE_UPDATE', data['email'])
            except Exception as error:
                send_statistic('ACTIVE_UPDATE', 'settings_send failed: email ' + 'email'
                               + str(data['email']) + str(error))
        if 'SiglentIP' in data:
            try:
                print(data['SiglentIP'])
                SiglentIP = str(data['SiglentIP'])
            except Exception as error:
                send_statistic('ACTIVE_UPDATE', 'settings_send failed: SiglentIP ' + 'SiglentIP'
                               + str(data['SiglentIP']) + str(error))
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'send_settings_on_settings_page() failed: whole thing ' + str(error))


def wifi_check():
    print("internet check")
    try:
        req = requests.get('http://clients3.google.com/generate_204')
        if req.status_code != 204:
            req = requests.get('http://google.com/')
            if req != 200:
                return False
            else:  # double check
                return True
        else:
            return True
    except Exception as error:
        print("internet issue")
        print(error)
        return False


def check_for_auth():
    try:
        global AUTHENTICATION
        print("User Authentication check")
        if AUTHENTICATION == 1:
            print("Pass")
            return True
        else:
            print("FAIL")
            return False
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'check_for_auth() failed. ' + str(error))


def getPublicIP():
    try:
        endpoint = 'https://ipinfo.io/json'
        response = requests.get(endpoint, verify=True)
        if response.status_code != 200:
            return 'Status:', response.status_code, 'Problem with the request. Exiting.'
        data = response.json()
        return data['ip']
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'getPublicIP() failed. ' + str(error))


def run_command():
    print("checking command")
    global COMMAND
    print(COMMAND)
    if COMMAND != '0':
        # reply with the subprocess might be cool
        print("command ran")
        try:
            response = subprocess.check_output(str(COMMAND), shell=True)
            send_statistic('ACTIVE_UPDATE', "COMMAND RESPONSE: " + response.decode("utf-8"))
            send_statistic('command', '0')
        except subprocess.CalledProcessError as err:
            send_statistic('ACTIVE_UPDATE', str(err))


def restart_15():
    try:
        t3 = threading.Thread(target=restart)
        t3.start()
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'restart_15() failed. ' + str(error))


def restart():
    try:
        time.sleep(15)
        os.system('sudo reboot')
        print("restarted")
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'restart() failed. ' + str(error))


def send_statistic(statistic, value):
    global PATH_TO_POST_TO, auth_key
    try:
        dictToSend = {'auth_key': auth_key,
                      'Analytics': {statistic: value}}
        headers = {'Content-type': 'application/json'}
        requests.post(url=PATH_TO_POST_TO, json=dictToSend, headers=headers)
    except Exception as error:
        print('send_statistic failed: ' + str('statistic: ' + statistic) +
              str('value: ' + value) + str(error))


###########################################################################
######################### MODIFIES FILES ##################################
###########################################################################


def update():
    global HOME_PATH, WEB_LATEST_UPDATE, URL_FOR_UPDATE
    try:
        NEW_PRJ_PATH = HOME_PATH + "FractalWebUI" + '_' + str(WEB_LATEST_UPDATE)
        answer = subprocess.check_output('if test -d ' + NEW_PRJ_PATH + '; then echo "exist"; fi ', shell=True)
        if str(answer).__contains__("exist"):
            os.system("sudo rm -R " + NEW_PRJ_PATH)  # erasing what it's operating on
            write_update(URL_FOR_UPDATE, NEW_PRJ_PATH)
            send_statistic('force_Update', 0)
            os.system('sudo reboot')
        else:
            write_update(URL_FOR_UPDATE, NEW_PRJ_PATH)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'update() failed. ' + 'WEB_LATEST_UPDATE: ' + str(WEB_LATEST_UPDATE)
                       + 'HOME_PATH: ' + str(HOME_PATH) + 'URL_FOR_UPDATE: ' + str(URL_FOR_UPDATE) + str(error))


def update_check():
    print("Update check")
    global MY_CURRENT_VERSION, WEB_LATEST_UPDATE, FORCE_UPDATE
    try:
        if FORCE_UPDATE == 1:
            print("force update")
            update()
            return True
        else:
            if MY_CURRENT_VERSION < int(WEB_LATEST_UPDATE):
                print("new update")
                update()
                send_statistic('my_current_version', str(WEB_LATEST_UPDATE))
                restart_15()
                return True
        print("no new update")
        return False
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'update_check() failed. ' + 'MY_CURRENT_VERSION: ' + str(MY_CURRENT_VERSION)
                       + 'WEB_LATEST_UPDATE: ' + str(WEB_LATEST_UPDATE) + 'FORCE_UPDATE: ' + str(FORCE_UPDATE)
                       + str(error))


def write_update(git, NEW_PRJ_PATH):
    global HOME_PATH
    try:
        os.system('cd')
        os.system('git clone ' + git + ' ' + NEW_PRJ_PATH)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'write_update, cd/git failed. ' + str('HOME_PATH: ' + HOME_PATH)
                       + str('git: ' + git) + str('NEW_PRJ_PATH: ' + NEW_PRJ_PATH) + str(error))
    try:
        with open('/lib/systemd/system/webserver.service', 'w') as file:
            content = \
                '''
                [Unit]
                Description=WebServer
                After=multi-user.target
    
                [Service]
                Environment=DISPLAY=:0.0
                Environment=XAUTHORITY=''' + HOME_PATH + '''.Xauthority
                Type=simple
                ExecStart=/usr/bin/python3''' + ' ' + NEW_PRJ_PATH + '''/run.py
                Restart=on-abort
                User=kiosk
    
                [Install]
                WantedBy=multi-user.target    
                '''
            file.write(content)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'write_update file update failed. ' + str('HOME_PATH: ' + HOME_PATH)
                       + str('git: ' + git) + str('NEW_PRJ_PATH: ' + NEW_PRJ_PATH) + str('content: ' + content)
                       + str(error))
    # update permissions for settings folder
    command = "chmod -R o+rw " + HOME_PATH + NEW_PRJ_PATH + "/Dashboard/_settings"
    try:
        os.system(command)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'write_update permission update failed:  ' + str('HOME_PATH: ' + HOME_PATH)
                       + str('git: ' + git) + str('NEW_PRJ_PATH: ' + NEW_PRJ_PATH)
                       + str('command: ' + command) + str(error))


def load__profile():  # only called once, afterwards authentication thread and dl + save settings takes
    global filePath_public_settings, userPrivateProfile, filePath_private_settings, HOME_PATH, PATH_TO_POST_TO, USER_NAME, WIFI_DRIVER_NAME, \
         ADMIN_EMAIL, ADMIN_PHONE
    HOME_PATH = readJsonValueFromKey("HOME_PATH", filePath_public_settings)  # get home path
    # if Private Profile not created, create it
    userPrivateProfile = HOME_PATH + "DashboardSettings.json"  # /home/kiosk/DashboardSettings.json
    answer = subprocess.check_output('if test -f ' + userPrivateProfile + '; then echo "exist"; fi ', shell=True)
    if not str(answer).__contains__("exist"):
        os.system("cp " + filePath_private_settings + " " + userPrivateProfile)
    # Public Profile
    PATH_TO_POST_TO = readJsonValueFromKey("PATH_TO_POST_TO", filePath_public_settings)
    print(PATH_TO_POST_TO)
    ADMIN_EMAIL = readJsonValueFromKey("ADMIN_EMAIL", filePath_public_settings)
    ADMIN_PHONE = readJsonValueFromKey("ADMIN_PHONE", filePath_public_settings)
    # Private Profile
    USER_NAME = readJsonValueFromKey("USER_NAME", userPrivateProfile)
    WIFI_DRIVER_NAME = readJsonValueFromKey("WIFI_DRIVER_NAME", userPrivateProfile)
    # Private Pofile
    # USER_NAME = readJsonValueFromKey("USER_NAME", filePath_private_settings)
    # print(USER_NAME)
    # WIFI_DRIVER_NAME = readJsonValueFromKey("WIFI_DRIVER_NAME", filePath_private_settings)


def Download_Profile():  # Runs on loop (authentication-thread)
    global AUTHENTICATION, SIGLENT, COMMAND, FORCE_UPDATE, URL_FOR_UPDATE, WEB_LATEST_UPDATE, \
        ADMIN_EMAIL, ADMIN_PHONE, PATH_TO_POST_TO, auth_key, MY_CURRENT_VERSION
    ######### DL Variables #########
    dictToSend = {'auth_key': auth_key,
                  'GET': {'Request': 'Profile'}}
    headers = {'Content-type': 'application/json'}
    print("headers")
    try:
        res = requests.post(url=PATH_TO_POST_TO, json=dictToSend, headers=headers)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'Profile POST error, this confirms POST is working. ' + str(error))

    try:
        profileData = res.json()
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'Profile GET returned non JSON. ' + str(error))
    try:
        AUTHENTICATION = profileData['authenticated']
        print("here")
        print(AUTHENTICATION)
        SIGLENT = profileData['siglent']
        COMMAND = profileData['command']
        FORCE_UPDATE = profileData['force_Update']
        URL_FOR_UPDATE = profileData['update_git_url']
        WEB_LATEST_UPDATE = profileData['version']
        MY_CURRENT_VERSION = profileData['my_current_version']
        ADMIN_EMAIL = profileData['admin_email']
        ADMIN_PHONE = profileData['admin_phone']
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'Profile GET returned with non updateable variables. ' + str(error))


def updateJsonFile(Key, Value, filePath):
    try:
        jsonFile = open(filePath, "r")
        data = json.load(jsonFile)  # Read the JSON into the buffer
        jsonFile.close()
        # Update Key & Value
        data[Key] = Value
        # Save changes to JSON file
        jsonFile = open(filePath, "w+")
        jsonFile.write(json.dumps(data))
        jsonFile.close()
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'updateJsonFile() failed. ' + str(filePath)
                       + str('Key: ' + Key) + str('Value: ' + Value) + str(error))


def readJsonValueFromKey(Key, filePath):
    try:
        f = open(filePath)
        data = json.load(f)
        f.close()
        return data[Key]
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'readJsonValueFromKey() failed. ' + str(filePath)
                       + str('Key: ' + Key) + str(error))


def plug_Wifi(data):
    ssid = data['wifi_ssid']
    password = data['wifi_pass']
    try:
        with open('/etc/netplan/50-cloud-init.yaml', 'w') as file:
            content = \
                '''network:
                    ethernets:
                        eth0:
                            dhcp4: true
                            dhcp4 - overrides:
                                route - metric: 200
                            optional: true
                    version: 2
                    wifis:
                      ''' + WIFI_DRIVER_NAME + ''':
                        optional: true
                        access-points:
                          "''' + ssid + '''":
                            password: "''' + password + '''"
                        dhcp4: true
                        dhcp4 - overrides:
                            route - metric: 100'''
        file.write(content)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'plug_Wifi() failed. ' + str('ssid: ' + ssid) + str('password: ' + password)
                       + str('content: ' + content) + str(error))
    print("Write successful. Rebooting now.")
    restart_15()


def plug_timer(data):
    global userPrivateProfile
    try:
        updateJsonFile('USER_TIMER', data['set-time'], userPrivateProfile)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'plug_timer() failed. ' + str('filePath: ' + userPrivateProfile)
                       + str('set-time: ' + data['set-time']) + str(error))


def plug_alarm(data):
    global userPrivateProfile
    try:
        updateJsonFile('USER_ALARM', data, userPrivateProfile)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'plug_alarm() failed. ' + str('filePath: ' + userPrivateProfile)
                       + str('data: ' + data) + str(error))

###########################################################################
############################### THREADS ###################################
###########################################################################


def BackgroundAuthCheck():
    global ONCE_INDEX
    print("bk check")
    print(threading.active_count())
    try:
        if wifi_check():
            Download_Profile()
            if check_for_auth():
                return True
            else:
                restart_15()
                print("authentication failed")
        else:
            restart_15()
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'BackgroundAuthCheck() Error. ' + 'ONCE_INDEX: ' + str(ONCE_INDEX) + str(error))


def authentication_thread():
    try:
        total_minutes = 1
        while total_minutes > 0:
            time.sleep(60)
            total_minutes -= 1
        BackgroundAuthCheck()
        authentication_thread()
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'authentication_thread() Error. ' + str(error))


def run_timer():
    try:
        if timer_state == "ON":
            timer_thread("stop")
        elif timer_state == "OFF":
            timer_thread("start")
        else:  # Initialization
            timer_thread("start")
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'run_timer() Error. ' + str(error))


def button_controller(data):
    global alarm_state, timer_state, MODE_PROCESS_IS_RUNNING
    print(data)
    try:
        if "timerButton" in data:
            if timer_state == "ON":
                timer_thread("stop")
            elif timer_state == "OFF":
                timer_thread("start")
            else:  # Initialization
                timer_thread("start")
            results = {'processed': 'true'}
            return jsonify(results)
        if "alarmButton" in data:
            if alarm_state == "ON":
                alarm_thread("stop")
            elif alarm_state == "OFF":
                alarm_thread("start")
            else:  # Initialization
                alarm_thread("start")
            results = {'processed': 'true'}
            return jsonify(results)
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'button_controller() Failed. ' + 'alarm_state: ' + str(alarm_state)
                       + 'timer_state: ' + str(timer_state) + 'MODE_PROCESS_IS_RUNNING: ' + str(MODE_PROCESS_IS_RUNNING)
                       + str(error))


time_t1 = 0
time_a1 = 0


def timer_thread(mode):
    global t2, timer_state, time_t1
    try:
        if mode == "start":
            time_t1 = time.time()
            pyTasks.timer.stop_threads = False
            t2 = threading.Thread(target=pyTasks.timer.timer_start)
            t2.start()
            while MODE_PROCESS_IS_RUNNING:
                time.sleep(0.02)
            MODE("ON")
            timer_state = "ON"
        if mode == "stop":
            time2 = time.time()
            if (time2 - time_t1) > 10:
                send_statistic('TIMERS_USED', '1')
            pyTasks.timer.stop_threads = True
            t2.join()
            while t2.is_alive():
                time.sleep(0.07)  # works well but javascript front end isn't connected or aligned.
            while MODE_PROCESS_IS_RUNNING:
                time.sleep(0.02)
            MODE("OFF")
            timer_state = "OFF"
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'timer_thread() Failed. ' + 'mode: ' + str(mode)
                       + 'timer_state: ' + str(timer_state) + str(error))


def alarm_thread(mode):
    global t1, alarm_state, SIGLENT, MODE_PROCESS_IS_RUNNING, time_a1
    try:
        if mode == "start":
            time_a1 = time.time()
            pyTasks.alarm.stop_threads = False
            t1 = threading.Thread(target=pyTasks.alarm.alarm_start)
            t1.start()
            # turn everything off
            while MODE_PROCESS_IS_RUNNING:
                time.sleep(0.02)
            MODE("OFF")
            MODE_PROCESS_IS_RUNNING = True  # stops all options running
            Signal_Generator_Controller("MHS_POWER_OFF")
            power_supply_amp_("OFF")
            time.sleep(0.07)
            alarm_state = "ON"
        if mode == "stop":
            time2 = time.time()
            if (time2 - time_a1) < 30:
                send_statistic('ALARMS_USED', '1')
            pyTasks.alarm.stop_threads = True
            t1.join()
            while t1.is_alive():
                time.sleep(0.07)
            power_supply_amp_("ON")
            if SIGLENT == 0:
                Signal_Generator_Controller("MHS_POWER_ON")
            time.sleep(2)  # maybe something better
            MODE_PROCESS_IS_RUNNING = False  # allows things to run again
            alarm_state = "OFF"
    except Exception as error:
        send_statistic('ACTIVE_UPDATE', 'alarm_thread() Failed. ' + 'mode: ' + str(mode)
                       + 'alarm_state: ' + str(alarm_state) + str(error))

# Notes to self:
# check all css/js links for any that need internet and download them
# check for corrupted files?
# try everything so if there is errors
#
