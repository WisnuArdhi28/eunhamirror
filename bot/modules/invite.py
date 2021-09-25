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
s = """
PERMISSION=push
echo "$1" | grep -e '$' > /dev/null;
CODE=$1
set -- $CODE
GITHUB_TOKEN=$1
GITHUB_USER_NAME=$2
GITHUB_ORG_NAME=$3
INVITEE_USERNAME=$4
REPO_TO_INVITE=$5
bash curl -i -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$GITHUB_ORG_NAME/$REPO_TO_INVITE/collaborators/$INVITEE_USERNAME" -X PUT -d "{\"permission\":\"$PERMISSION\"}" 2>&1 | grep message || echo "Sent Invite To $INVITEE_USERNAME to Join $REPO_TO_INVITE"
"""
f.write(s)
f.close()
os.chmod(bashfile, 0o755)
bashcmd=bashfile
for arg in sys.argv[1:]:
  bashcmd += ' '+arg

def invite(update: Update, context: CallbackContext):
    message = update.effective_message
    cmd = message.text.split(' ', 1)
    CHAT_ID=message.chat_id
    print(CHAT_ID)
    if len(cmd) == 1:
        message.reply_text('Please Provide Username And Repo Name To Invite A GitHub User')
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        bashcmd + ' ' + '"' + GITHUB_TOKEN + ' ' + GITHUB_USER_NAME + ' ' + GITHUB_ORG_NAME + ' ' + cmd + '"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    reply = ''
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*Inviting User To Mentioned GitHub Repo*\n\n '{stdout}'\n"
        LOGGER.error(f"Shell - {bashcmd} {GITHUB_TOKEN} {GITHUB_USER_NAME} {GITHUB_ORG_NAME} {cmd}- {stderr}")
    if stderr:
        reply += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {bashcmd} {GITHUB_TOKEN} {GITHUB_USER_NAME} {GITHUB_ORG_NAME} {cmd}- {stderr}")
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


INVITE_HANDLER = CommandHandler(['inv', 'invite'], invite,
                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
dispatcher.add_handler(INVITE_HANDLER)
