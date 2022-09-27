from Dashboard import threading, time, pyTasks, os, requests, json, subprocess, jsonify

#  GLOBALS
t1 = threading.Thread  # alarm thread
t2 = threading.Thread  # timer thread
timer_state = None  # Global Variable
alarm_state = None  # Global Variable
ON_start = 0
ON_end = 0
##### Load from Profile #####
HOME_PATH = None  # Path to /home/kiosk
USER_NAME = None
PATH_TO_POST_TO = None  # None
WIFI_DRIVER_NAME = None
MY_CURRENT_VERSION = None
WAVEFORM_LOADED = None
##### Download from web #####
ADMIN_EMAIL = None
ADMIN_PHONE = None
AUTHENTICATION = None
COMMAND = None
SIGLENT = None
FORCE_UPDATE = None
URL_FOR_UPDATE = None
WEB_LATEST_UPDATE = None
##### Extra variables #######
ONCE_INDEX = 0
POWER_GEN_STATE = 0
MODE_PROCESS_IS_RUNNING = False
MODE_STATE = None
auth_key = 'klshdfgkjh(*&89y(*YF^*&%&RIUHEFIH986893yh4rjfskjdhffhgajkdfni&*%&^^IUJhknfga'


# GLOBALS

# if index is refreshed it may keep threads running may want to kill them unless index will never refresh

###########################################################################
############################ FIRST CHECK ##################################
###########################################################################


def start_index():
    global ONCE_INDEX, AUTHENTICATION, WAVEFORM_LOADED, SIGLENT
    if ONCE_INDEX == 0:  # have we done this once?
        load__profile()  # load all profile/global variables
        if wifi_check():  # WiFi Check
            Download_Profile()
            send_statistic('IP', str(getPublicIP()))  # Send IP Address - Web Server
            print("wifi pass")
            print("profile downloaded")
            print("IP obtained")
            if check_for_auth():  # comes first from the profile  # if profile says 0
                if WAVEFORM_LOADED == 0:
                    send_statistic('ACTIVE_UPDATE', 'Signal was not loaded, loading...')
                    Signal_Generator_Controller("LOAD")
                if update_check():  # if update do update stuff
                    return "Update"
                threading.Thread(target=authentication_thread).start()  # start authentication loop thread
                power_supply_amp_("ON")  # turn amp on when we authenticate
                if SIGLENT == "1":  # if siglent on then pass powering signal generator
                    Signal_Generator_Controller("SIGLENT_POWER_ON")
                else:
                    Signal_Generator_Controller("MHS_POWER_ON")  # turn on signal generator
                ONCE_INDEX = "1"  # remember we have already loaded all we need
                return "Authenticated"
            else:
                Signal_Generator_Controller("UNLOAD")  # signal generator has to be on
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
    global SIGLENT, ON_start, ON_end, MODE_PROCESS_IS_RUNNING, MODE_STATE
    if mode == "ON":
        if MODE_PROCESS_IS_RUNNING:  # does this eliminate the need for ajax
            return
        if MODE_STATE == "ON":
            return
        MODE_PROCESS_IS_RUNNING = True
        MODE_STATE = "ON"
        send_statistic('TOTAL_TIMES_USED', "1")
        ON_start = time.time()
        if SIGLENT == "1":  # if siglent on then pass siglent signal
            Signal_Generator_Controller("SIGLENT_ON")
        else:
            Signal_Generator_Controller("MHS_ON")  # pass signal generator
        speaker_protection_("ON")
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
        if SIGLENT == "1":  # if siglent on then pass siglent signal off
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
    global POWER_GEN_STATE, HOME_PATH, WAVEFORM_LOADED
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
        pass
        time.sleep(.4)
    elif mode == "SIGLENT_OFF":
        pass
        time.sleep(.4)
    elif mode == "SIGLENT_POWER_ON":
        pass  # most definitely turning on another relay for power
        time.sleep(.4)
    elif mode == "SIGLENT_POWER_OFF":
        pass  # can I power it on and off from ethernet?
        time.sleep(.4)
    elif mode == "LOAD":
        if POWER_GEN_STATE == "0":
            Signal_Generator_Controller("MHS_POWER_ON")
            time.sleep(25)
        else:
            os.system(
                'sudo ' + HOME_PATH + 'new-mhs5200a-12-bits/setwave5200 /dev/ttyUSB0 ' + HOME_PATH +
                '/.local/phi.csv ' + '0')
            time.sleep(.8)
            updateJsonFile("SIGNAL_IN_GENERATOR_MEMORY", "1",
                           os.path.dirname(os.path.abspath(__file__)) + "/_settings/profile.json")
    elif mode == "UNLOAD":
        print("unload " + str(WAVEFORM_LOADED))
        if WAVEFORM_LOADED == "1":
            if POWER_GEN_STATE == "0":
                Signal_Generator_Controller("MHS_POWER_ON")
                time.sleep(25)
            else:
                os.system(
                    'sudo ' + HOME_PATH + 'new-mhs5200a-12-bits/setwave5200 /dev/ttyUSB0 ' + HOME_PATH +
                    '/.local/zero.csv ' + '0')
                time.sleep(.8)
                updateJsonFile("SIGNAL_IN_GENERATOR_MEMORY", "0",
                               os.path.dirname(os.path.abspath(__file__)) + "/_settings/profile.json")


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
        MY_CURRENT_VERSION, WAVEFORM_LOADED, ADMIN_EMAIL, ADMIN_PHONE, AUTHENTICATION, COMMAND, SIGLENT, FORCE_UPDATE, \
        URL_FOR_UPDATE, WEB_LATEST_UPDATE, ONCE_INDEX, POWER_GEN_STATE, MODE_PROCESS_IS_RUNNING, MODE_STATE, auth_key
    if 'troubleshoot' in data:
        message = "HOME_PATH: " + str(HOME_PATH) + " USER_NAME: " + str(USER_NAME) + " PATH_TO_POST_TO: " + str(
            PATH_TO_POST_TO) + " WIFI_DRIVER_NAME: " + str(WIFI_DRIVER_NAME) + " MY_CURRENT_VERSION: " + str(
            MY_CURRENT_VERSION) + " WAVEFORM_LOADED: " + str(WAVEFORM_LOADED) + " ADMIN_EMAIL: " + str(ADMIN_EMAIL) + \
                  " ADMIN_PHONE: " + str(ADMIN_PHONE) + " AUTHENTICATION: " + str(AUTHENTICATION) + \
                  " COMMAND: " + str(COMMAND) + " SIGLENT: " + str(SIGLENT) + " FORCE_UPDATE: " + str(FORCE_UPDATE) + \
                  " URL_FOR_UPDATE: " + str(URL_FOR_UPDATE) + " WEB_LATEST_UPDATE: " + str(WEB_LATEST_UPDATE) + \
                  " POWER_GEN_STATE: " + str(POWER_GEN_STATE) + " MODE_PROCESS_IS_RUNNING: " + str(MODE_PROCESS_IS_RUNNING) + \
                  " MODE_STATE: " + str(MODE_STATE) + " auth_key: " + str(auth_key)
        send_statistic('ACTIVE_UPDATE', message)
        test_string = "Path= what to send"
        # file size # sub process lsblk
        HDD_size = str(subprocess.check_output('lsblk', shell=True))
        # IP address
    if 'email' in data:
        send_statistic('ACTIVE_UPDATE', data['email'])
        # send text whatever I want


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
    except:
        print("internet issue")
        # render error message
        return False


def check_for_auth():
    global AUTHENTICATION
    print("User Authentication check")
    if AUTHENTICATION == 1:
        print("Pass")
        return True
    else:
        print("FAIL")
        return False


def getPublicIP():
    endpoint = 'https://ipinfo.io/json'
    response = requests.get(endpoint, verify=True)
    if response.status_code != 200:
        return 'Status:', response.status_code, 'Problem with the request. Exiting.'
    data = response.json()
    return data['ip']


def run_command():  # test
    print("running command")
    global COMMAND
    if COMMAND != '0':
        # reply with the subprocess might be cool
        print("command ran")
        try:
            send_statistic('ACTIVE_UPDATE', subprocess.check_output(COMMAND))
        except subprocess.CalledProcessError as err:
            send_statistic('ACTIVE_UPDATE', err)


def restart_15():
    t3 = threading.Thread(target=restart)
    t3.start()


def restart():
    time.sleep(15)
    os.system('sudo reboot')
    print("restarted")
    # try, catch, kill thread, display error


def send_statistic(statistic, value):
    global PATH_TO_POST_TO, auth_key
    dictToSend = {'auth_key': auth_key,
                  'Analytics': {statistic: value}}
    headers = {'Content-type': 'application/json'}
    res = requests.post(url=PATH_TO_POST_TO, json=dictToSend, headers=headers)


###########################################################################
######################### MODIFIES FILES ##################################
###########################################################################


def update():
    global HOME_PATH, WEB_LATEST_UPDATE, URL_FOR_UPDATE
    NEW_PRJ_PATH = HOME_PATH + "update" + '_' + str(WEB_LATEST_UPDATE)
    answer = subprocess.check_output('if test -d ' + NEW_PRJ_PATH + '; then echo "exist"; fi ', shell=True)
    if str(answer).__contains__("exist"):
        os.system("sudo rm -R " + NEW_PRJ_PATH)  # erasing what it's operating on
    write_update(URL_FOR_UPDATE, NEW_PRJ_PATH)


def update_check():
    print("Update check")
    global HOME_PATH, MY_CURRENT_VERSION, WEB_LATEST_UPDATE, URL_FOR_UPDATE, FORCE_UPDATE
    if FORCE_UPDATE == 1:
        print("force update")
        update()
        restart_15()  # gives 15 seconds to complete the below to return
        send_statistic('force_Update', 0)
        os.system('sudo reboot')
        return True
    else:
        if MY_CURRENT_VERSION < int(WEB_LATEST_UPDATE):
            print("new update")
            update()
            restart_15()  # gives 15 seconds to complete the below to return
            send_statistic('my_current_version', str(WEB_LATEST_UPDATE))
            os.system('sudo reboot')
            return True
    print("no new update")
    return False


def write_update(git, NEW_PRJ_PATH):
    global HOME_PATH
    os.system('cd')
    os.system('git clone ' + git + ' ' + NEW_PRJ_PATH)
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
    # update permissions for settings folder
    os.system("chmod -R o+rw " + HOME_PATH + NEW_PRJ_PATH + "/Dashboard/_settings")


def load__profile():  # only called once, afterwards authentication thread and dl + save settings takes
    global HOME_PATH, PATH_TO_POST_TO, USER_NAME, WIFI_DRIVER_NAME, WAVEFORM_LOADED, \
        ADMIN_EMAIL, ADMIN_PHONE
    DefaultPath = os.path.dirname(os.path.abspath(__file__)) + "/_settings/profile.json"
    HOME_PATH = readJsonValueFromKey("HOME_PATH", DefaultPath)
    filePath = HOME_PATH + "profile.json"  # /home/kiosk/profile.json
    answer = subprocess.check_output('if test -d ' + filePath + '; then echo "exist"; fi ', shell=True)
    if not str(answer).__contains__("exist"):
        os.system("cp " + DefaultPath + " " + filePath)
    PATH_TO_POST_TO = readJsonValueFromKey("PATH_TO_POST_TO", filePath)  # remove this/ switch it over
    USER_NAME = readJsonValueFromKey("USER_NAME", filePath)
    WIFI_DRIVER_NAME = readJsonValueFromKey("WIFI_DRIVER_NAME", filePath)
    WAVEFORM_LOADED = readJsonValueFromKey("WAVEFORM_LOADED", filePath)
    ADMIN_EMAIL = readJsonValueFromKey("ADMIN_EMAIL", filePath)
    ADMIN_PHONE = readJsonValueFromKey("ADMIN_PHONE", filePath)


def Download_Profile():  # Runs on loop (authentication-thread)
    global AUTHENTICATION, SIGLENT, COMMAND, FORCE_UPDATE, URL_FOR_UPDATE, WEB_LATEST_UPDATE, \
        ADMIN_EMAIL, ADMIN_PHONE, PATH_TO_POST_TO, auth_key, MY_CURRENT_VERSION
    ######### DL Variables #########
    dictToSend = {'auth_key': auth_key,
                  'GET': {'Request': 'Profile'}}
    headers = {'Content-type': 'application/json'}
    res = requests.post(url=PATH_TO_POST_TO, json=dictToSend, headers=headers)
    profileData = res.json()
    AUTHENTICATION = profileData['authenticated']
    SIGLENT = profileData['siglent']
    COMMAND = profileData['command']
    FORCE_UPDATE = profileData['force_Update']
    URL_FOR_UPDATE = profileData['update_git_url']
    WEB_LATEST_UPDATE = profileData['version']
    MY_CURRENT_VERSION = profileData['my_current_version']
    ADMIN_EMAIL = profileData['admin_email']
    ADMIN_PHONE = profileData['admin_phone']
    run_command()  # Only called once and from here.


def updateJsonFile(Key, Value, filePath):
    jsonFile = open(filePath, "r")
    data = json.load(jsonFile)  # Read the JSON into the buffer
    jsonFile.close()
    # Update Key & Value
    data[Key] = Value
    # Save changes to JSON file
    jsonFile = open(filePath, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()


def readJsonValueFromKey(Key, filePath):
    f = open(filePath)
    data = json.load(f)
    f.close()
    return data[Key]


def plug_Wifi(data):
    ssid = data['wifi_ssid']
    password = data['wifi_pass']
    with open('/etc/netplan/50-cloud-init.yaml', 'w') as file:
        content = \
            '''network:
                ethernets:
                    eth0:
                        dhcp4: true
                        optional: true
                version: 2
                wifis:
                  ''' + WIFI_DRIVER_NAME + ''':
                    optional: true
                    access-points:
                      "''' + ssid + '''":
                        password: "''' + password + '''"
                    dhcp4: true'''
        file.write(content)
    print("Write successful. Rebooting now.")
    restart_15()



def plug_timer(data):
    filePath = os.path.dirname(os.path.abspath(__file__)) + "/_settings/profile.json"
    updateJsonFile('USER_TIMER', data['set-time'], filePath)


def plug_alarm(data):
    filePath = os.path.dirname(os.path.abspath(__file__)) + "/_settings/profile.json"
    updateJsonFile('USER_ALARM', data, filePath)


###########################################################################
############################### THREADS ###################################
###########################################################################


def BackgroundAuthCheck():
    global WAVEFORM_LOADED, ONCE_INDEX
    print("bk check")
    print(threading.active_count())
    if wifi_check():
        Download_Profile()
        if check_for_auth():
            if WAVEFORM_LOADED == 0:
                Signal_Generator_Controller("LOAD")
            return True
        else:
            Signal_Generator_Controller("UNLOAD")
            restart_15()
            print("authentication failed")
    else:
        restart_15()


def authentication_thread():
    total_minutes = 60
    while total_minutes > 0:
        time.sleep(60)
        total_minutes -= 1
    BackgroundAuthCheck()
    authentication_thread()


def run_timer():
    if timer_state == "ON":
        timer_thread("stop")
    elif timer_state == "OFF":
        timer_thread("start")
    else:  # Initialization
        timer_thread("start")


def button_controller(data):
    global alarm_state, timer_state, MODE_PROCESS_IS_RUNNING
    print(data)
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


def timer_thread(mode):
    global t2, timer_state, time_t1
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
        if (time2 - time_t1) < 10:
            send_statistic('TIMERS_USED', '1')
        pyTasks.timer.stop_threads = True
        t2.join()
        while t2.is_alive():
            time.sleep(0.07)  # works well but javascript front end isn't connected or aligned.
        while MODE_PROCESS_IS_RUNNING:
            time.sleep(0.02)
        MODE("OFF")
        timer_state = "OFF"


def alarm_thread(mode):
    global t1, alarm_state, MODE_PROCESS_IS_RUNNING, time_a1
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
        Signal_Generator_Controller("MHS_POWER_ON")
        time.sleep(2)  # maybe something better
        MODE_PROCESS_IS_RUNNING = False  # allows things to run again
        alarm_state = "OFF"

# Notes to self:
# check all css/js links for any that need internet and download them
# check for corrupted files?
# try everything so if there is errors
#
