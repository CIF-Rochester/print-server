import os
import logging

import argparse
import tempfile

import img2pdf

from flask import Flask, request, redirect, url_for, render_template
from subprocess import run
from datetime import datetime
import paramiko
import PyPDF2
import math
import time
from pymupdf import Pixmap
from werkzeug.utils import secure_filename
from config import load_config, Config
import pymupdf

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CFG_PATH = os.path.join(SCRIPT_PATH, "config.cfg")
PDF_TO_IMAGE_DPI = 600

BACKGROUND_COLOR="#0f0f0f"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

app = Flask(__name__)

def makeLogger(logFile):
    formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logFile)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

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

def printFile(file, pages, orientation, per_page, copies):
    # return 0
    command = ['lpr',file,f'-#{copies}','-o', 'fit-to-page', '-o', f'number-up={per_page}', '-P', config.printer.printer_name]
    #^ Auto fit to page, provide custom scale later
    if pages:
        command.extend(['-o',f'page-ranges={pages}'])
    if orientation=='Landscape':
        command.extend(['-o','orientation-requested=4'])
    ret = run(command)
    time.sleep(5)
    return ret

def update_storage():
    current_time = datetime.now()
    files = os.listdir(config.logging.file_storage_path)
    for file in files:
        if (current_time - datetime.strptime(file[:file.index("---")],'%H.%M.%S_%m-%d-%Y')).total_seconds() > config.logging.file_storage_time:
            os.remove(f"{config.logging.file_storage_path}/{file}")

def allZeros(retCodes):
    for retCode in retCodes:
        if retCode != 0:
            return False
    return True

def convert_to_black_and_white(path, num_pages):
    images = []
    with tempfile.TemporaryDirectory() as temp_dir:  # Saves images temporarily in disk rather than RAM to speed up parsing
        # Converting pages to images
        input = pymupdf.open(path)
        for i in range(num_pages):
            pix = input.load_page(i).get_pixmap(dpi=PDF_TO_IMAGE_DPI)
            gray_pix = Pixmap(pymupdf.csGRAY, pix)
            img_path = os.path.join(temp_dir, f"page_{i}.png")
            gray_pix.save(img_path)
            images.append(img_path)
        input.close()
        os.remove(path)

        with open(path, "bw") as gray_pdf:
            gray_pdf.write(img2pdf.convert(images))

def notify_discord(txt: str, time: str):
    index = txt.index(" - File:")
    user = txt[:index]
    txt = f"[{time}]  {txt[(index + 3):]}"
    try:
        client.connect(config.nauticock.ip, username=config.nauticock.username, password=config.nauticock.password, timeout=30)
        client.exec_command(config.nauticock.command + f" --user \"{user}\" --text \"{txt}\"")
        client.close()
    except Exception as e:
        logger.error("Unable to connect to notify NauticockBot")

def upload_file(username):
    retCodes = []
    try:
        update_storage()
        pages = request.form.get('pages').replace(" ","")
        color = request.form.get('color')
        ornt  = request.form.get('orientation')
        per_page = int(request.form.get('perpage'))
        copies = int(request.form.get('copies'))
        files = request.files.getlist('file')
        total_pages = 0
        for file in files:
            if not file or file.filename == '':
                return render_template('error.html', error="No file attached", username=username, color=BACKGROUND_COLOR)
            if file.filename[-4:] != '.pdf':
                return render_template('error.html', error="Attached file is not pdf", username=username, color=BACKGROUND_COLOR)
            current_time = datetime.now()
            time_string_file = current_time.strftime('%H.%M.%S_%m-%d-%Y')
            filename = f"{time_string_file}---{secure_filename(file.filename)}"
            newpath = os.path.join(config.logging.file_storage_path, filename)
            file.save(newpath)

            pdf_reader = PyPDF2.PdfReader(file)
            pg = len(pdf_reader.pages)

            if color == 'Black and White':
                convert_to_black_and_white(newpath, pg)

            # log things

            txt = f"{username} - File: {file.filename}"
            if copies != 1:
                txt += f", {copies} copies"
            txt += f", {pg} pages"
            if pages:
                txt += f", {pages} pages printed"
            if per_page != 1:
                txt += f", {per_page} per page"
            if color == 'Black and White':
                txt += ", grayscale"

            try:
                total_pages += copies * math.ceil(parsePages(pages, pg) / per_page)
            except Exception as e:
                txt += ", CANNOT PARSE SPECIFIED PAGES"
                logger.error(txt)
                return render_template('error.html', error="Cannot parse specified pages", username=username, color=BACKGROUND_COLOR)
            if total_pages > config.print_limitations.max_pages:
                txt += f", PAGE LIMIT OF {config.print_limitations.max_pages} EXCEEDED"
                logger.error(txt)
                notify_discord(txt, time_string_file)
                return render_template('error.html',
                                       error=f"Page limit of {config.print_limitations.max_pages} exceeded",
                                       username=username, color=BACKGROUND_COLOR)
            try:
                ret = printFile(newpath,pages,ornt, per_page, copies)
            except Exception as e:
                txt += ", FAILED TO RUN SUBPROCESS"
                logger.error(txt)
                if total_pages > config.print_limitations.discord_threshold:
                    notify_discord(txt, time_string_file)
                return render_template('error.html', error="Failed to run subprocess", username=username, color=BACKGROUND_COLOR)
            retCodes.append(ret.returncode)
            if ret.returncode != 0:
                txt += f", PRINT FAILED WITH EXIT CODE {ret.returncode}"
                logger.error(txt)
                if total_pages > config.print_limitations.discord_threshold:
                    notify_discord(txt, time_string_file)
                return render_template('error.html', error="lpr command error - Please turn on printer", color=BACKGROUND_COLOR)
            if total_pages > config.print_limitations.discord_threshold:
                notify_discord(txt, time_string_file)
            logger.info(txt)

    except Exception as e:
        return render_template('error.html', error=str(e), username=username, color=BACKGROUND_COLOR)
    return render_template('success.html', username=username, color=BACKGROUND_COLOR)

@app.route('/', methods=['GET', 'POST'])
def update_file():
    if request.method == 'GET':
        return render_template('login.html', color=BACKGROUND_COLOR)
    if request.form['submit-button'] == 'Login':
        username = request.form.get("username")
        password = request.form.get("password")
        client.connect(config.citadel.ip, username=config.citadel.username, password=config.citadel.password,
                       timeout=30)
        stdin, stdout, stderr = client.exec_command(f"echo {password} | kinit {username}")
        outline = stdout.readlines()
        errline = stderr.readlines()
        if outline and not any("incorrect" in s for s in errline) and not any("not found" in s for s in errline):
            client.close()
            return render_template('index.html', username=username, color=BACKGROUND_COLOR)
        else:
            client.close()
            return render_template('login.html', color=BACKGROUND_COLOR)
    elif request.form['submit-button'] == 'Print':
        return upload_file(request.form.get("username"))
    else:
        return render_template('index.html', username=request.form.get("username"), color=BACKGROUND_COLOR)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Print server for remotely printing to CIF lab printer")
    parser.add_argument('--config', '-c', help='Path to print server config file.', default=DEFAULT_CFG_PATH)

    args = parser.parse_args()

    path_to_cfg = args.config
    config: Config = load_config(path_to_cfg)
    logger = makeLogger(config.logging.log_path)
    if not os.path.exists(config.logging.file_storage_path):
        os.makedirs(config.logging.file_storage_path)


    # from waitress import serve
    # serve(app,host='0.0.0.0',port=8080)
    # gunicorn -w 4 'web_printer:app' -b '0.0.0.0:8080'
    app.run(host='0.0.0.0', port=5000,debug=False)
