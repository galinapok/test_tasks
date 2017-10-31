#! /usr/bin/python
# -*- coding: utf-8 -*-
"""Module to build  code from P4"""

import os
import sys
import configparser
from shutil import copy
import platform
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import subprocess
import smtplib
from P4 import P4
from P4 import P4Exception

def read_config(config_file):
    """
        Get config from file
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    deport_path = config["p4"]["deport_path"]
    port = config["p4"]["port"]
    p4_user = config["p4"]["user"]
    p4_password = config["p4"]["password"]
    smtp_user = config["smtp"]["User"]
    smtp_password = config["smtp"]["Password"]
    smtp_port = config["smtp"]["Port"]
    smtp_ssl = config["smtp"]["SMTP_SSL"]
    smtp_server = config["smtp"]["Server"]
    recipient = config["smtp"]["Recipient"]
    return  deport_path, port, p4_user, p4_password, smtp_port, smtp_user, smtp_password, \
            smtp_ssl, smtp_server, recipient




def check_for_updates(p4, deport_path):
    """
        Connnects to P4
        Get latest version fron P4
    """
    with p4.connect():
        p4.client = "auto-build-ws"
        client = p4.fetch_client()
        client["Root"] = os.getcwd()
        p4.save_client(client)
        try:
            p4.run("sync", "-n", deport_path)
        except P4Exception:
            for warning in p4.warnings:
                if "up-to-date" in warning:
                    print("No changes since last run")
                    sys.exit(0)
            for error in p4.errors:
                print(error)
                sys.exit(1)

        p4.run("sync", "-f", "//test/proj1/...")


def create_dest_folder(path):
    """
        Create build folder
    """
    dest_folder = os.path.join(path, "bin")
    print(dest_folder)
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    if  (platform.system()) == "Windows":
        folder_list = [x[0].split('\\')[-1] for x in os.walk(dest_folder) \
                        if  x[0] != dest_folder]
    else:
        folder_list = [x[0].split('/')[-1] for x in os.walk(dest_folder) \
        if  x[0] != dest_folder]

    print(folder_list)
    if len(folder_list) < 1:
        dir_name = os.path.join(dest_folder, "1")
    else:
        print(folder_list)
        folder_list.sort(key=int)
        dir_name = os.path.join(dest_folder, str(int(folder_list[-1]) + 1))

    os.makedirs(dir_name)
    return dir_name


def run_build(deport_path):
    """
        Run buils using build script
    """

    path = "{}{}".format(os.getcwd(), deport_path.replace("//", "/").replace('...', ""))
    if  (platform.system()) == "Windows":
        filepath = os.path.join(path, "build.bat")
    else:
        filepath = os.path.join(path, "build.sh")

    execute_build = subprocess.Popen(filepath, cwd=path, shell=False,
                                     stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = execute_build.communicate()
    if execute_build.returncode > 0:
        print("build faild")
        return  "", stdout, stderr
    else:
        dest_folder = create_dest_folder(path)
        copy(os.path.join(path, "HelloWorld.class"), dest_folder)
    return dest_folder, "", ""


def submit_changes(p4, dir_name):
    """
        Submit changes to P4
    """
    with p4.connect():
        changespec = p4.fetch_change()
        changespec["Description"] = "Add build artifact."
        ret = p4.save_change(changespec)
        new_cl = ret[0].split(" ")[1]
        p4.run_add('-c', new_cl, os.path.join(dir_name, "HelloWorld.class"))
        p4.run("submit", "-c", new_cl)


def send_email(server, user, pwd, recipient, body, ssl, smtp_port):
    """
        Send email in case of fail
    """

    if ssl:
        server = smtplib.SMTP_SSL(server, smtp_port)
    else:
        server = smtplib.SMTP(server, smtp_port)

    server.login(user, pwd)
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = recipient
    msg['Subject'] = "Build failed"
    message = body
    msg.attach(MIMEText(message))
    server.sendmail(user, recipient, msg.as_string())




def main():
    """
        Main
    """
    deport_path, port, p4_user, p4_password, smtp_port, smtp_user,\
    smtp_password, smtp_ssl, smtp_server, recipient = read_config("config.ini")
    p4 = P4()
    p4.user = p4_user
    p4.password = p4_password
    p4.port = port
    check_for_updates(p4, deport_path)
    dir_name, stdout, stderr = run_build(deport_path)
    if dir_name == "":
        send_email(smtp_server, smtp_user, smtp_password,
                   recipient, str(stderr), smtp_ssl, smtp_port)
        sys.exit(0)
    submit_changes(p4, dir_name)


if __name__ == "__main__":
    main()
