import os
import logging

from flask import Flask, request, redirect, url_for, render_template
from subprocess import run
from datetime import datetime
import subprocess
import paramiko
import PyPDF2
import math
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'FILE_STORE'
PRINTER_NAME = 'Brother_HL_L3280CDW_series_USB'
MAX_PAGES = 50
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

logger = makeLogger('printer.log')

def parsePages(str, total_pages):
    if str == '':
        return total_pages
    elif str.isnumeric():
        page = int(str)
        return 1 if page > 0 and page < total_pages else 0
    elif "," in str:
        substrings = str.split(",")
        pages = 0
        for substring in substrings:
            pages += parsePages(substring, total_pages)
    else:
        index = str.index("-")
        start = int(str[:index])
        end = int(str[index+1:])
        return max(1, min(end, total_pages)) - min(total_pages, max(1, start)) + 1

def printFile(file,pages,orientation,per_page, copies):
    # return 0
    command = ['lpr',file,f'-#{copies}','-o', 'fit-to-page', '-o', f'number-up={per_page}', '-P', 'Brother_HL_L3280CDW_series_USB']
    #^ Auto fit to page, provide custom scale later
    if pages:
        command.extend(['-o',f'page-ranges={pages}'])
    if orientation=='Landscape':
        command.extend(['-o','orientation-requested=4'])
    ret = run(command)
    return ret

def update_storage():
    current_time = datetime.now()
    files = os.listdir(UPLOAD_FOLDER)
    for file in files:
        if (current_time - datetime.strptime(file[:file.index("---")],'%H.%M.%S_%m-%d-%Y')).total_seconds() > FILE_SAVE_TIME:
            os.remove(f"{UPLOAD_FOLDER}/{file}")

def allZeros(retCodes):
    for retCode in retCodes:
        if retCode != 0:
            return False
    return True

def upload_file(username):
    retCodes = []
    error = ""
    try:
        pages = request.form.get('pages').replace(" ","")
        ornt  = request.form.get('orientation')
        per_page = int(request.form.get('perpage'))
        copies = int(request.form.get('copies'))
        files = request.files.getlist('file')
        total_pages = 0
        for file in files:
            if not file or file.filename == '':
                update_storage()
                return render_template('error.html', error="No file attached", username=username)
            if file.filename[-4:] != '.pdf':
                update_storage()
                return render_template('error.html', error="Attached file is not pdf", username=username)
            pdf_reader = PyPDF2.PdfReader(file)
            print_pages = len(pdf_reader.pages)
            try:
                total_pages += parsePages(pages, print_pages)
            except Exception as e:
                return render_template('error.html', error="Cannot parse specified pages", username=username)
        total_pages = math.ceil(total_pages / per_page)
        total_pages *= copies
        if total_pages > MAX_PAGES:
            return render_template('error.html', error=f"Page limit of {MAX_PAGES} exceeded", username=username)
        for file in files:
            current_time = datetime.now()
            time_string_file = current_time.strftime('%H.%M.%S_%m-%d-%Y')
            time_string_log = current_time.strftime('%I:%M:%S %p %m-%d-%Y')
            filename = f"{time_string_file}---{secure_filename(file.filename)}"
            newpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            file.save(newpath)

            # log things
            pdf_reader = PyPDF2.PdfReader(file)
            pg = len(pdf_reader.pages)
            txt = f"[{time_string_log}] {username} - File: {file.filename}"
            if copies != 1:
                txt += f", {copies} copies"
            txt += f", {pg} pages"
            if pages:
                txt += f", {pages} pages printed"
            if per_page != 1:
                txt += f", {per_page} per page"

            ret = printFile(newpath,pages,ornt, per_page, copies)
            retCodes.append(ret)
            if ret != 0:
                txt += ", PRINT FAILED"
            logger.info(txt)

        if not allZeros(retCodes):
            update_storage()
            return render_template('error.html', error="lpr command error - Please turn on printer")

    except Exception as e:
        print(e)
        update_storage()
        return render_template('error.html', error=str(e), username=username)
    update_storage()
    return render_template('success.html', username=username)

@app.route('/', methods=['GET', 'POST'])
def update_file():
    if request.method == 'GET':
        return render_template('login.html')
    if request.form['submit-button'] == 'Login':
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            client.connect("citadel.cif.rochester.edu", username=username, password=password, timeout=30)
        except Exception as e:
            return render_template('login.html')
        else:
            return render_template('index.html', username=username)
    elif request.form['submit-button'] == 'Print':
        return upload_file(request.form.get("username"))
    else:
        return render_template('index.html', username=request.form.get("username"))

if __name__ == '__main__':
    # from waitress import serve
    # serve(app,host='0.0.0.0',port=8080)
    # gunicorn -w 4 'web_printer:app' -b '0.0.0.0:8080'
    app.run(host='0.0.0.0', port=8080,debug=True)
