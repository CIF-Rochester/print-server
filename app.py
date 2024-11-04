import os
import logging
from logging import exception

from flask import Flask, request, redirect, url_for, render_template
from paramiko.ssh_exception import SSHException
from werkzeug.utils import secure_filename
from python_freeipa import ClientMeta, Client, AuthenticatedSession
from subprocess import run
from datetime import datetime
import subprocess
import paramiko
import requests
from requests.auth import HTTPBasicAuth

UPLOAD_FOLDER = 'FILE_STORE'
PRINTER_NAME = 'Brother_HL_L3280CDW_series_USB'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def makeLogger(logFile):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logFile)
    logger.addHandler(fh)
    return logger

logger = makeLogger('webprinter.log')
def getNumberOfPage(pdfFile):
    t = subprocess.run(f"pdfinfo {pdfFile}  | awk \"/^Pages:/ {{print $2}}\"",shell=True,stdout=subprocess.PIPE)#,text=True)
    v = t.stdout.strip()
    try:
        v = v.decode()
    except (UnicodeDecodeError, AttributeError):
        pass
    return v

# check the list of available printers with `lpstat -p -d` 
# pass the particular printer with `-P` flag to `lpr`


def printFile(file,pages,orientation,per_page):
    # return 0
    command = ['lpr',file,'-o', 'fit-to-page', '-o', f'number-up={per_page}', '-P', 'Brother_HL_L3280CDW_series_USB']
    #^ Auto fit to page, provide custom scale later
    if pages:
        command.extend(['-o',f'page-ranges={pages}'])
    if orientation=='Landscape':
        command.extend(['-o','orientation-requested=4'])
    ret = run(command)
    return ret.returncode

def upload_file(username):
    retCodes = []
    try:
        pages = request.form.get('pages')
        ornt  = request.form.get('orientation')
        per_page = request.form.get('perpage')
        for file in request.files.getlist('file'):

            if not file or file.filename == '':
                return render_template('result.html', printer=PRINTER_NAME, data="No file attached")
            filename = secure_filename(file.filename)
            newpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            file.save(newpath)
            # print(newpath)

            # log things
            pg = getNumberOfPage(newpath)
            txt = f"{username}, [{datetime.now().strftime('%I:%M:%S %p %d-%m-%Y')}] - File: {file}, Total No. of pages: {pg} "
            if pages: txt += f"Pages to print: {pages} "
            if per_page: txt += f"Per page: {per_page}"
            logger.info(txt)

            ret = printFile(newpath,pages,ornt,per_page)
            retCodes.append(ret)

        if all(retCodes)==0:
            txt = "Print job submitted successfully"
        else:
            txt = "Unable to submit print job"

    except Exception as e:
        print(e)
        txt = "Unable to submit print job"

    return render_template('result.html', printer=PRINTER_NAME, data=txt)

@app.route('/', methods=['GET', 'POST'])
def update_file():
    if request.method == 'GET':
        return render_template('login.html', printer=PRINTER_NAME)
    if request.form['submit-button'] == 'Login':
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            client.connect("citadel.cif.rochester.edu", username=username, password=password, timeout=-1)
        except SSHException:
            return render_template('login.html', printer=PRINTER_NAME)
        else:
            return render_template('index.html', printer=PRINTER_NAME, username=username)
    else:
        return upload_file(request.form.get("username"))

if __name__ == '__main__':
    # from waitress import serve
    # serve(app,host='0.0.0.0',port=8080)
    # gunicorn -w 4 'web_printer:app' -b '0.0.0.0:8080'
    app.run(host='0.0.0.0', port=8080,debug=True)
