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
DUMP_TYPE=public #Set this to either public or private #Fork This Repo and also fork this repo: https://github.com/mirrordump/dumpyara.git
##DO NOT EDIT
DUMMY_VARIABLE=1
ORIGINAL_PATH=$(pwd)
ORIGINAL_GITHUB_USER_EMAIL=$(git config user.email)
ORIGINAL_GITHUB_USER_NAME=$(git config user.name)
URL=$1
GIT_TOKEN=$2
GITHUB_USER_NAME=$3
GITHUB_REPO_NAME=$4
GITHUB_USER_EMAIL=$5
TELEGRAM_CHANNEL_NAME=$6
DUMPER_REPO_WORKFLOW_URL=$7
CHAT_ID=$8
USER_ID=$9
USER_FIRST_NAME=${10}
USER_TAG=${11}

git config --global user.email "$GITHUB_USER_EMAIL"
git config --global user.name "$GITHUB_USER_NAME"
git config --global credential.helper cache
if [[ $URL == *://*/* ]] ; then true ; else echo "Incorrect Link Format! Do Not Abuse This Feature!" && exit 1 ; fi
SIZE=$(curl -sI --head --location $URL | grep -i content-length | awk '{print $2}') && SIZE=`echo $SIZE | sed 's/\\r//g'` #removing \r due to html
HUMAN_SIZE=$(timeout 0.5s numfmt --to=iec $SIZE) && HUMAN_SIZE=$(echo $HUMAN_SIZE'B')
if [ -z $SIZE ]; then
    echo "Dump Failed!
    You Havent Provided A Proper link, Do Not Abuse This Feature With Your Random Requests, You Might Lose Access To This Feature If You Abuse It!"
    exit 1
fi
if [[ $SIZE -lt 400000000 ]]; then
  echo "Your File is Too Small $HUMAN_SIZE. It Can Also Be Possible That Your Link Failed Auto-Verification And Hence Is Unsupported, In That Case, Try Mirroring It And Then Dumping!"
  exit 1
fi
rm -rf $GITHUB_REPO_NAME
git clone --quiet --depth=1 --single-branch https://$GITHUB_USER_NAME:$GIT_TOKEN@github.com/$GITHUB_USER_NAME/$GITHUB_REPO_NAME.git
CHECK=$(tail -n 1 $GITHUB_REPO_NAME/.github/workflows/dumpyara.yml)
echo '  'ROM_URL: $URL >> CHECK.txt
VERIFY=$(tail -n 1 CHECK.txt) && rm CHECK.txt
if [ "$CHECK" == "$VERIFY" ]
then
    echo "
    DUMP FAILED! The Link Provided was Previously Dumped Already, Please do not Misuse this Feature!
    "
    exit 1
elif [ "$DUMP_TYPE" == private ]
then
    cd $GITHUB_REPO_NAME/.github/workflows && sed -i '$d' dumpyara.yml
    echo '  'ROM_URL: $URL >> dumpyara.yml
    cd ../.. && echo 'Dummy File To Push Dumped Firmware to Private Github Repo' > private.txt
    echo "$CHAT_ID" > CHAT_ID.txt
    echo "$USER_ID" > USER_ID.txt
    echo "$USER_TAG" > USER_TAG.txt
    echo "$USER_FIRST_NAME" > USER_FIRST_NAME.txt
    git add -f .
    echo $URL > CLEAN.txt && CLEAN=$(sed 's/^.*\///' CLEAN.txt) && CLEAN=$(echo "${CLEAN%.*}") && rm CLEAN.txt
    git commit --quiet -m "Dump $CLEAN"
    git push --quiet -f https://$GITHUB_USER_NAME:$GIT_TOKEN@github.com/$GITHUB_USER_NAME/$GITHUB_REPO_NAME
    echo "$DUMPER_REPO_WORKFLOW_URL"
elif [ "$DUMP_TYPE" == public ]
then
    cd $GITHUB_REPO_NAME/.github/workflows && sed -i '$d' dumpyara.yml
    echo '  'ROM_URL: $URL >> dumpyara.yml
    cd ../.. && rm -rf private.txt
    echo "$CHAT_ID" > CHAT_ID.txt
    echo "$USER_ID" > USER_ID.txt
    echo "$USER_TAG" > USER_TAG.txt
    echo "$USER_FIRST_NAME" > USER_FIRST_NAME.txt
    git add -f .
    echo $URL > CLEAN.txt && CLEAN=$(sed 's/^.*\///' CLEAN.txt) && CLEAN=$(echo "${CLEAN%.*}") && rm CLEAN.txt
    git commit --quiet -m "Dump $CLEAN"
    git push --quiet -f https://$GITHUB_USER_NAME:$GIT_TOKEN@github.com/$GITHUB_USER_NAME/$GITHUB_REPO_NAME
    echo "$DUMPER_REPO_WORKFLOW_URL"
else
    echo "
    Fill in the Variable 'DUMP_TYPE with either public or private!
    "
    exit 1
fi
#CLEANUP TIME!
git config --global user.email "$ORIGINAL_GITHUB_USER_EMAIL"
git config --global user.name "$ORIGINAL_GITHUB_USER_NAME"
cd $ORIGINAL_PATH
rm -rf $GITHUB_REPO_NAME
"""
f.write(s)
f.close()
os.chmod(bashfile, 0o755)
bashcmd=bashfile
for arg in sys.argv[1:]:
  bashcmd += ' '+arg

def dump(update: Update, context: CallbackContext):
    message = update.effective_message
    cmd = message.text.split(' ', 1)
    CHAT_ID=message.chat_id
    USER_ID = f"{message.from_user.id}"
    FIRST_NAME = f"{message.from_user.first_name}"
    if message.from_user.username:
        USER_TAG = f"@{message.from_user.username}"
    else:
        USER_TAG = f"none"
    print(CHAT_ID)
    if len(cmd) == 1:
        message.reply_text('Please Provide a Direct Link to an Android Firmware')
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        bashcmd + ' ' + '"' + cmd + '" "' + GITHUB_TOKEN + '" "' + GITHUB_USER_NAME + '" "' + GITHUB_DUMPER_REPO_NAME + '" "' + GITHUB_USER_EMAIL + '" "' + TELEGRAM_CHANNEL_NAME + '" "' + DUMPER_REPO_WORKFLOW_URL + '" "' + str(CHAT_ID) + '" "' + USER_ID + '" "' + FIRST_NAME + '" "' + USER_TAG + '"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    reply = ''
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*Dumping Your Given Firmware, Please wait, Dump will be availaible on \n\n{TELEGRAM_CHANNEL_NAME}*\n\n '{stdout}'\n"
        LOGGER.info(f"Shell - {bashcmd} {cmd} {GITHUB_TOKEN} {GITHUB_USER_NAME} {GITHUB_DUMPER_REPO_NAME} {GITHUB_USER_EMAIL} {TELEGRAM_CHANNEL_NAME} {DUMPER_REPO_WORKFLOW_URL} {str(CHAT_ID)} - {stdout}")
    if stderr:
        reply += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {bashcmd} {cmd} {GITHUB_TOKEN} {GITHUB_USER_NAME} {GITHUB_DUMPER_REPO_NAME} {GITHUB_USER_EMAIL} {TELEGRAM_CHANNEL_NAME} {DUMPER_REPO_WORKFLOW_URL} {str(CHAT_ID)} - {stderr}")
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


DUMP_HANDLER = CommandHandler(['dmp', 'dump'], dump,
                    filters=CustomFilters.owner_filter | CustomFilters.authorized_user | CustomFilters.sudo_user, run_async=True)
dispatcher.add_handler(DUMP_HANDLER)
