from Dashboard import app, os

if __name__ == "__main__":
    os.system("sudo /usr/bin/systemctl restart screensaver.service")
    app.run(host='127.0.0.1', port=5000, debug=True)
