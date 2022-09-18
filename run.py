from Dashboard import app, os, socketio

if __name__ == "__main__":
    # get_data()
    os.system("sudo /usr/bin/systemctl restart screensaver.service")
    # app.run(debug=True)
    socketio.run(app, host='127.0.0.1', port=5000)
