import os
import logging

from flask import Flask, request, redirect, url_for, render_template
from paramiko.ssh_exception import SSHException
from subprocess import run
from datetime import datetime
import subprocess
import paramiko
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'FILE_STORE'
PRINTER_NAME = 'Brother_HL_L3280CDW_series_USB'
# save time in seconds
FILE_SAVE_TIME = 7 * 24 * 60 * 60

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


def printFile(file,pages,orientation,per_page, copies):
    # return 0
    command = ['lpr',file,'-o', 'fit-to-page', '-o', f'number-up={per_page}', '-P', 'Brother_HL_L3280CDW_series_USB']
    #^ Auto fit to page, provide custom scale later
    if pages:
        command.extend(['-o',f'page-ranges={pages}'])
    if orientation=='Landscape':
        command.extend(['-o','orientation-requested=4'])
    retCodes = []
    for i in range(copies):
        ret = run(command)
    return retCodes

def update_files():
    current_time = datetime.now()
    files = os.listdir(UPLOAD_FOLDER)
    for file in files:
        if (current_time - datetime.strptime(file[:file.index("---")],'%H.%M.%S_%d-%m-%Y')).total_seconds() > FILE_SAVE_TIME:
            os.remove(f"{UPLOAD_FOLDER}/{file}")


def upload_file(username):
    retCodes = []
    try:
        pages = request.form.get('pages')
        ornt  = request.form.get('orientation')
        per_page = int(request.form.get('perpage'))
        copies = int(request.form.get('copies'))
        for file in request.files.getlist('file'):
            if not file or file.filename == '':
                return render_template('result.html', printer=PRINTER_NAME, data="No file attached")
            current_time = datetime.now()
            time_string_file = current_time.strftime('%H.%M.%S_%d-%m-%Y')
            time_string_log = current_time.strftime('%I:%M:%S %p %d-%m-%Y')
            filename = f"{time_string_file}---{secure_filename(file.filename)}"
            newpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            file.save(newpath)

            # log things
            pg = getNumberOfPage(newpath)
            txt = f"[{time_string_log}] {username} - File: {file.filename}"
            if copies != 1:
                txt += f", {copies} copies"
            txt += f", {pg} pages"
            if pages:
                txt += f", {pages} pages printed"
            if per_page != 1:
                txt += f", {per_page} per page"
            logger.info(txt)

            ret = printFile(newpath,pages,ornt,per_page, copies)
            retCodes.append(ret)

        if all(retCodes)==0:
            txt = "Print job submitted successfully"
        else:
            txt = "Unable to submit print job"

    except Exception as e:
        print(e)
        txt = "Unable to submit print job"
    update_files()
    return render_template('result.html', data=txt)

@app.route('/', methods=['GET', 'POST'])
def update_file():
    if request.method == 'GET':
        return render_template('login.html')
    if request.form['submit-button'] == 'Login':
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            client.connect("citadel.cif.rochester.edu", username=username, password=password, timeout=-1)
        except SSHException:
            return render_template('login.html')
        else:
            return render_template('index.html', username=username)
    else:
        return upload_file(request.form.get("username"))

if __name__ == '__main__':
    # from waitress import serve
    # serve(app,host='0.0.0.0',port=8080)
    # gunicorn -w 4 'web_printer:app' -b '0.0.0.0:8080'
    app.run(host='0.0.0.0', port=8080,debug=True)
