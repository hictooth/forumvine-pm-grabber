import MySQLdb
import forumvine
import traceback
import time
import os
import json
import sys
import subprocess

SAVE_FILE = None

def getMessages(username, password):
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            saveData = json.load(f)
        currentMessages = saveData['messages']
        currentIDs = saveData['ids']
        forumvine.allMessages = currentMessages
        forumvine.doneIDs = currentIDs

    try:
        messages = forumvine.getPms(username, password)
        print(len(messages))
        return messages
    except:
        traceback.print_exc()
        currentIDs = forumvine.doneIDs
        currentMessages = forumvine.allMessages
        saveData = {'ids': currentIDs, 'messages': currentMessages}
        with open(SAVE_FILE, 'w') as f:
            json.dump(saveData, f)
        sys.exit(0)


def threadify(messages):
    threads = []

    # messages are already in sorted, combined order
    for message in messages:
        doneMessage = False
        user1 = message['from_name']
        user2 = message['to_name']
        subject = message['subject']
        if subject.startswith('Re: '):
            subject = subject[4:]

        for thread in threads:
            tuser1 = thread['user1']
            tuser2 = thread['user2']
            tsubject = thread['subject']
            if tsubject.startswith('Re: '):
                tsubject = tsubject[4:]

            if (subject == tsubject) and ((user1 == tuser1 and user2 == tuser2) or (user1 == tuser2 and user2 == tuser1)):
                # this is the correct thread!
                thread['messages'].append(message)
                doneMessage = True

        if not doneMessage:
            # this message needs a new thread
            thread = {
                'user1': user1,
                'user2': user2,
                'subject': subject,
                'messages': [message],
                'top_id': message['id']
            }
            threads.append(thread)

    print(len(threads))
    return threads


# simple caching function to avoid lots of lookups
userMappings = {}
def getUserId(username):
    global userMappings
    if username in userMappings:
        return userMappings[username]

    cursor.execute("SELECT * FROM phpbb_users WHERE username=%s", [username])
    users = cursor.fetchall()
    if len(users) == 0:
        return False

    id = users[0]['user_id']
    userMappings[username] = id
    return id


def messigify(threads):
    # and now we've got threads, convert them back into messages!
    allMessages = []

    for thread in threads:
        messages = thread['messages']
        isFirst = True

        for i in range(0, len(messages)):
            message = messages[i]

            # fix 'top_id' attribute
            if isFirst:
                message['top_id'] = 0
                isFirst = False
            message['top_id'] = thread['top_id']

            # fix 'has_reply' attribute
            hasReply = i < (len(messages)-1)
            message['has_reply'] = hasReply

            # fic user ids
            message['from_id'] = getUserId(message['from_name'])
            message['to_id'] = getUserId(message['to_name'])

            allMessages.append(message)

    return allMessages


def insertMessages(messages):
    # used to actually insert the messages into the db!
    #
    # annoyingly, we have to use php to insert them because we need access to
    # some php specific phpbb functions. Therefore we've created the file
    # 'insert.php' which takes messages saved in a 'messages.json' file, and
    # inserts them into the database.

    # write messages to a file
    with open('messages.json', 'w') as f:
        json.dump(messages, f)

    # run the php file
    subprocess.call(['/usr/bin/php', '/home/hictooth/pm-grabber/insert.php'])

    # delete the messages file
    os.remove('messages.json')


def processUser(userRow):
    # set the save file name
    global SAVE_FILE
    SAVE_FILE = str(userRow['user_id']) + '.json'

    # get the messages
    username = userRow['tt_username']
    password = userRow['tt_password']
    messages = getMessages(username, password)

    # process the messages
    threads = threadify(messages)
    messages = messigify(threads)

    # insert the messages into the db
    insertMessages(messages)

    # update the user row
    sql = "UPDATE phpbb_users SET import_status=3 WHERE user_id=%s"
    cursor.execute(sql, [str(userRow['user_id'])])
    db.commit()

    # remove the tmp file
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)



db = MySQLdb.connect("127.0.0.1", "dbuser", "dbpassword", "db")
cursor = db.cursor(MySQLdb.cursors.DictCursor)

sql = "SELECT * FROM phpbb_users WHERE import_status=2"
cursor.execute(sql)

users = cursor.fetchall()
if len(users) > 0:
    processUser(users[0])
