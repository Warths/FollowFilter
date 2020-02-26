from utils import log
import twitch_channel
import network
from network.irc.irc import Irc
import time
import json
import requests

log.warning("This program assume perfect user input. Please Double check your inputs")
log.notice("Follow Bot Removal tool.")
log.notice("Please enter YOUR channel name.")

# Getting USER_ID by name
LOGIN = input("Username >> ").strip()
USER = network.twitch_api.get_user_id_by_login(LOGIN)['data'][0]['id']

# Starting Initial checks
channel = twitch_channel.TwitchChannel(USER)
channel.detect_bot()

# Listing all follow blob
amount = 0
blob_list = []
for follow in channel.follows:
    if channel.follows[follow]['flags']['in_follow_blob']:
        blob_list.append(channel.follows[follow]['user']['name'])
        amount += 1

log.log('Writing follow blob to file..')
# Writing all names to a file
with open("follow_blob.txt", 'w') as file:
    file.write("\n".join(blob_list))

log.notice('All follow blob has been written to follow_blob.txt')
log.notice('Remove potentials false-negative and type enter to continue')
input()

# Retrieving all names still in file
log.notice("Reopening follow_blob.txt..")
with open("follow_blob.txt", 'r') as file:
    blob_list = file.readlines()
    for i in range(0, len(blob_list)):
        blob_list[i] = blob_list[i].strip("\n")
    while "" in blob_list:
        blob_list.remove("")

log.notice(f"{len(blob_list)} username to ban.")
print(blob_list)

log.notice(f"Get a user_blocks_edit enabled token and past it here :")
log.notice(f"This token will be used to block-unblock flagged accounts")
oauth = input(">>").strip()
print(oauth)

tasks = len(blob_list) * 2
log.notice(f"This will take ~{round(tasks * 0.2 /60)} minutes")


log.log("Rebuilding User_id list")
user_id_blob_list = []
for account in blob_list:
    for user_id in channel.follows:
        if account == channel.follows[user_id]['user']['name']:
            user_id_blob_list.append(user_id)

headers = {"Client-id": twitch_channel.twitch_api.CLIENT_ID,
           'Authorization': 'OAuth ' + oauth}

for user_id in user_id_blob_list:
    tasks -= 1
    log.log(f"blocking {account} [{tasks} task(s) remaining ~ {round(tasks * 0.2 /60)} minutes]")
    r = requests.put(f"https://api.twitch.tv/v5/users/{USER}/blocks/{user_id}", headers=headers)
    log.discrete(f"Status code: {r.status_code}")
    log.discrete(f"{r.content}")

for unblock_user_id in user_id_blob_list:
    tasks -= 1
    log.log(f"Unblocking {account} [{tasks} task(s) remaining ~ {round(tasks * 0.2 /60)} minutes]")
    r = requests.delete(f"https://api.twitch.tv/v5/users/{USER}/blocks/{user_id}", headers=headers)
    log.discrete(f"{r.content}")


log.notice("Completed.")
