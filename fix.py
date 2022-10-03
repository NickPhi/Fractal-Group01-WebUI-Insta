# File to fix
import os
import subprocess
import time


def fix():
    print("started")
    x = 0
    while True:
        filePath = "/home/kiosk/FractalWebUI_" + str(x)
        answer = subprocess.check_output('if test -d ' + filePath + '; then echo "exist"; fi ', shell=True)
        if not str(answer).__contains__("exist"):
            # found highest x that doesn't exist
            if x == 1:  # remember, 1 wouldn't exist here
                time.sleep(30)
                break  # issue, it's found no updates and it is broken
            resortToBackup(x-1)
            break
        x += 1


def resortToBackup(x):
    # old = "/home/kiosk/FractalWebUI_" + str(x)
    revised = "/home/kiosk/FractalWebUI_" + str(x-1)
    # os.system("sudo rm -R " + old)  # remove old update
    with open('/lib/systemd/system/webserver.service', 'w') as file:
        content = \
            '''
            [Unit]
            Description=WebServer
            After=multi-user.target

            [Service]
            Environment=DISPLAY=:0.0
            Environment=XAUTHORITY=/home/kiosk.Xauthority
            Type=simple
            ExecStart=/usr/bin/python3''' + ' ' + revised + '''/run.py
            Restart=on-abort
            User=kiosk

            [Install]
            WantedBy=multi-user.target    
            '''
        file.write(content)
    os.system("sudo reboot")


if __name__ == "__main__":
    fix()


# on bash loop
# fix is initiated if webserver.service fails
