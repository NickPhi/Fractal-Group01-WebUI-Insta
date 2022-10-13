import Dashboard.service
from Dashboard import app, threading, render_template, request, url_for, redirect, requests, re
from Dashboard.service import start_index, send_settings_on_settings_page, plug_Wifi, plug_timer, plug_alarm, \
    button_controller, MODE, alarm_thread, timer_thread, siglent_panel

Y = 0


@app.route('/', methods=['GET', 'POST'])
def index():
    global Y
    if request.method == 'GET':
        Status = start_index()
        Y = Dashboard.service.SCREEN_HEIGHT
        if Status == "Load_Index":
            return render_template('index.html', screen_height=Y)
        elif Status == "Authenticated":
            return render_template('index.html', screen_height=Y, local_storage_clear=1)
        elif Status == "Not-Authenticated":
            return render_template('payment.html',
                                   response=Dashboard.service.ADMIN_EMAIL + " " + Dashboard.service.ADMIN_PHONE)
        elif Status == "Update":
            return render_template('system_reboot.html', response='Updated your system')
        elif Status == "no-Wifi":
            return render_template('wifi.html')
    if request.method == 'POST':
        # Handles Alarm & Timer since we use AJAX to disable/enable when done
        btn_ajax_data = request.get_json()
        return button_controller(btn_ajax_data)


@app.route('/turnon')
def turnon():
    MODE("ON")
    return "Complete"


@app.route('/turnoff')
def turnoff():
    MODE("OFF")
    return "Complete"


@app.route('/test')
def test():
    dictToSend = {'auth': 'klshdfgkjh(*&89y(*YF^*&%&RIUHEFIH986893yh4rjfskjdhffhgajkdfni&*%&^^IUJhknfga',
                  "Profile": {'hello': "asdf"}
                  }
    res = requests.post('http://127.0.0.1:4999/user_secretURLss', json=dictToSend)
    print(res.text)
    return "asdf"


# @app.route('/alarm')
# def alarm():
#    run_alarm()
#    return "Complete"


# @app.route('/timer')
# def timer():
#    if request.method == 'POST':
#        print("called")
#        run_timer()
#        return "Complete"


@app.route('/settings.html', methods=['GET', 'POST'])
def settings():
    print(threading.active_count())
    if request.method == 'GET':
        return render_template("settings.html",
                               response=Dashboard.service.ADMIN_EMAIL + " " + Dashboard.service.ADMIN_PHONE)
    if request.method == 'POST':
        if 'siglent_panel' in request.form:
            if Dashboard.service.SIGLENT == 1:
                return render_template('siglent_panel.html')
        send_settings_on_settings_page(request.form)
        return render_template('index')
        return redirect(url_for('index'))


@app.route('/siglentIP.html', methods=['GET', 'POST'])
def siglentIP():
    if Dashboard.service.SIGLENT == 1:
        if request.method == 'GET':
            return render_template("siglentIP.html")
        if request.method == 'POST':
            # confirm IP address
            regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
            if re.search(regex, request.form['SiglentIP']):
                print("Valid Ip address")
                siglent_panel(request.form)
                return redirect(url_for('index'))
            else:
                print("Invalid Ip address")
                return render_template("siglentIP.html", invalid="Invalid IP Address, try again.")
    else:
        return redirect(url_for('index'))


@app.route('/siglent_panel.html', methods=['GET', 'POST'])
def route_siglent_panel():
    if Dashboard.service.SIGLENT == 1:
        if request.method == 'GET':
            return render_template("siglent_panel.html")
        if request.method == 'POST':
            siglent_panel(request.form)
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@app.route('/wifi.html', methods=['GET', 'POST'])
def wifi():
    if request.method == 'GET':
        return render_template('wifi.html')
    if request.method == 'POST':
        plug_Wifi(request.form)
        return render_template('system_reboot.html')


@app.route('/timer_settings', methods=['GET', 'POST'])
def timer_settings():
    if request.method == 'GET':
        if Dashboard.service.timer_state == "ON":
            timer_thread("stop")
        return render_template('timer_settings.html')
    if request.method == 'POST':
        plug_timer(request.form)
        return redirect(url_for('index'))


@app.route('/alarm_settings', methods=['GET', 'POST'])
def alarm_settings():
    if request.method == 'GET':
        if Dashboard.service.alarm_state == "ON":
            alarm_thread("stop")
        return render_template('alarm_settings.html')
    if request.method == 'POST':
        data = request.form
        print(data.get('set-time'))
        # alarm_thread("stop")  # works but if the stop takes a while the page feels non responsive
        plug_alarm(data.get('set-time'))
        return redirect(url_for('index'))


@app.route('/wifi_back.html', methods=['GET', 'POST'])
def wifi_back():
    if request.method == 'GET':
        return render_template('wifi_back.html')
    if request.method == 'POST':
        plug_Wifi(request.form)
        return render_template('system_reboot.html')
