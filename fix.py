# File to fix
import os
import subprocess

homePath = '/home/kiosk/'


def fix():
    try:
        print("started")
        answer = subprocess.check_output('ls ' + homePath, shell=True)
        s_list = answer.__str__().split('\\n')
        e_list = []
        for x in s_list:
            if x.__contains__('FractalWebUI'):
                cat = x.split('_')
                e_list.append(cat[1])
        print(e_list)
        e_list.sort()
        e_list.reverse()  # e_list[0] largest
        resortToBackup(e_list[0], e_list[1])  # old, new
    except Exception as error:
        print(error)


def resortToBackup(old, new):
    new = homePath + 'FractalWebUI_' + str(new)
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
            ExecStart=/usr/bin/python3''' + ' ' + new + '''/run.py
            Restart=on-abort
            User=kiosk

            [Install]
            WantedBy=multi-user.target    
            '''
        file.write(content)
    old = homePath + 'FractalWebUI_' + str(old)
    os.system("sudo rm -R " + old)  # remove old update
    os.system("sudo reboot")


if __name__ == "__main__":
    fix()


# on bash loop
# fix is initiated if webserver.service fails
