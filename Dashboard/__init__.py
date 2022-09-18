import os
import threading
import time
import json
import subprocess
from datetime import datetime, date
import requests
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import flask
from flask import Flask, render_template, request, jsonify, redirect, url_for

from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)

import Dashboard.service
import Dashboard.routes
import Dashboard.pyTasks.alarm
import Dashboard.pyTasks.timer

