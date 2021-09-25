import os
import sys
from functools import wraps
from bot import LOGGER, dispatcher
from bot import GITHUB_USER_NAME, GITHUB_TOKEN, GITHUB_DUMPER_REPO_NAME, TELEGRAM_CHANNEL_NAME, DUMPER_REPO_WORKFLOW_URL, GITHUB_USER_EMAIL, DATABASE_URL, user_data
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage

import subprocess
import string
import random

bashfile=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
bashfile='/tmp/'+bashfile+'.sh'
#CHAT_ID = update.effective_chat.id
f = open(bashfile, 'w')
s = """#!/bin/bash
ORIGINAL_PATH=$(pwd)
ORIGINAL_GIT_USER_EMAIL=$(git config user.email)
ORIGINAL_GIT_USER_NAME=$(git config user.name)
echo "$1" | grep -e '^\(https\?\|ftp\)://.*$' > /dev/null;
CODE=$1
set -- $CODE
GITHUB_TOKEN=$1
GITHUB_USER_NAME=$2
GITHUB_REPO_NAME=$3
GITHUB_USER_EMAIL=$4
TELEGRAM_CHANNEL_NAME=$5
CURRENT_CHAT_ID=$6
URL=$7
BRANCH=$8
URL_WITHOUT_HTTPS=$(echo "$URL" |sed 's/https\?:\/\///')
NEW_URL=https://${GITHUB_USER_NAME}:${GITHUB_TOKEN}@${URL_WITHOUT_HTTPS} #just incase its a dump from own private org
DUMP_NAME=$(echo $URL_WITHOUT_HTTPS | sed 's/.*\///')
git config --global user.email "$GITHUB_USER_EMAIL"
git config --global user.name "$GITHUB_USER_NAME"
git config --global credential.helper cache  
git ls-remote "$NEW_URL" > /dev/null 2>&1
if [ "$?" -ne 0 ]; then echo "[ERROR] "$NEW_URL" is not a git repo" && exit 1; fi
git clone --depth=1 --single-branch --quiet https://${GITHUB_USER_NAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USER_NAME}/${GITHUB_REPO_NAME} ~/tempdirectorysirbro
cd ~/tempdirectorysirbro
rm -rf BRANCH.txt URL.txt CURRENT_CHAT_ID.txt
echo "$CURRENT_CHAT_ID" > CURRENT_CHAT_ID.txt
echo "${URL}" > URL.txt
if [[ "${BRANCH}" == "" ]] ; then touch BRANCH.txt ; else echo "${BRANCH}" > BRANCH.txt && git add BRANCH.txt ; fi
git add URL.txt CURRENT_CHAT_ID.txt
git commit -m "Generate Dummy Tree Using $DUMP_NAME"
git push -f --quiet https://${GITHUB_USER_NAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USER_NAME}/${GITHUB_REPO_NAME}
cd ${ORIGINAL_PATH}
rm -rf ${GITHUB_REPO_NAME}
git config --global user.email "$ORIGINAL_GIT_USER_EMAIL"
git config --global user.name "$ORIGINAL_GIT_USER_NAME"
"""
f.write(s)
f.close()
os.chmod(bashfile, 0o755)
bashcmd=bashfile
for arg in sys.argv[1:]:
  bashcmd += ' '+arg

def dummy(update: Update, context: CallbackContext):
    message = update.effective_message
    cmd = message.text.split(' ', 1)
    CHAT_ID=message.chat_id
    print(CHAT_ID)
    if len(cmd) == 1:
        message.reply_text('Please Provide a Direct Link to an Android Dump')
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        bashcmd + ' ' + '"' + GITHUB_TOKEN + ' ' + GITHUB_USER_NAME + ' ' + GITHUB_DUMMY_REPO_NAME + ' ' + GITHUB_USER_EMAIL + ' ' + TELEGRAM_CHANNEL_NAME + ' ' + str(CHAT_ID) + ' ' + cmd + '"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    reply = ''
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*Generating Dummy Device-Tree, It will be availaible on \n\n{TELEGRAM_CHANNEL_NAME}*\n\n '{stdout}'\n"
        LOGGER.info(f"Shell - {bashcmd} {GITHUB_TOKEN} {GITHUB_USER_NAME} {GITHUB_DUMMY_REPO_NAME} {GITHUB_USER_EMAIL} {TELEGRAM_CHANNEL_NAME} {str(CHAT_ID)} {cmd} - {stdout}")
    if stderr:
        reply += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {bashcmd} {GITHUB_TOKEN} {GITHUB_USER_NAME} {GITHUB_DUMMY_REPO_NAME} {GITHUB_USER_EMAIL} {TELEGRAM_CHANNEL_NAME} {str(CHAT_ID)} {cmd} - {stderr}")
    if len(reply) > 3000:
        with open('shell_output.txt', 'w') as file:
            file.write(reply)
        with open('shell_output.txt', 'rb') as doc:
            context.bot.send_document(
                document=doc,
                filename=doc.name,
                reply_to_message_id=message.message_id,
                chat_id=message.chat_id)
    else:
        message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


DUMMY_HANDLER = CommandHandler(['dmy', 'dummy'], dummy,
                    filters=CustomFilters.owner_filter | CustomFilters.authorized_user | CustomFilters.sudo_user, run_async=True)
dispatcher.add_handler(DUMMY_HANDLER)
