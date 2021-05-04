from concurrent import futures

import app as app
from flask import Flask, render_template, request
import kolesa_pb2
import kolesa_pb2_grpc
import grpc
import requests
from bs4 import BeautifulSoup
import logging
import datetime
import sys
import os
import json
from logging.handlers import TimedRotatingFileHandler
import re

FORMATTER = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")

date = datetime.date.today().strftime('%Y%m%d')

FIRST = True
dirname = os.path.dirname(__file__)

dirname = os.path.join(dirname, 'logs')

if not os.path.exists(dirname):
    os.mkdir(dirname)

LOG_FILE = os.path.join(dirname, 'my_app.' + date + '.log')


def getFirst():
    global FIRST
    return FIRST


def setFirst(state):
    global FIRST
    FIRST = state


def getDate():
    global date
    return date


def namer(name):
    a = name[-28:][-8:]
    date = datetime.datetime.strptime(a, '%Y%m%d').date()
    date = date + datetime.timedelta(days=1)
    str_date = datetime.datetime.strftime(date, '%Y%m%d')
    name = name.replace('.' + getDate() + '.log', '') + '.log'
    return name.replace(a, str_date)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight', backupCount=10, encoding='utf-8')
    file_handler.suffix = '%Y%m%d'
    file_handler.namer = namer
    file_handler.extMatch = re.compile(r"^\d{8}$")

    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # better to have too much log than not enough
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger


logger = get_logger('Adil')


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


def run_service(phone):
    with grpc.insecure_channel('localhost:5001') as channel:
        stub = kolesa_pb2_grpc.KolesaScraperStub(channel)
        response = stub.LoadVirusLinks(kolesa_pb2.PhoneRequest(phone=phone))
        return response


app = Flask(__name__)


@app.route("/virus", methods=["GET"])
def hello():
    if request.method == "GET":
        phone = request.args.get('phone')
        c = f'{run_service(phone)}'
        return c.replace('\'', '').replace('\\','')


if __name__ == '__main__':
    app.run(debug=True, port=8000)
