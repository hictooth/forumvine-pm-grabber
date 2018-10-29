import xmlrpc.client
import ssl
import sys
import time

class CookiesTransportHttps(xmlrpc.client.SafeTransport):
    """A SafeTransport (HTTPS) subclass that retains cookies over its lifetime."""

    # Note context option - it's required for success
    def __init__(self, context=None):
        super().__init__(context=context)
        self._cookies = []

    def send_headers(self, connection, headers):
        if self._cookies:
            connection.putheader("Cookie", "; ".join(self._cookies))
        super().send_headers(connection, headers)

    def parse_response(self, response):
        # This check is required if in some responses we receive no cookies at all
        if response.msg.get_all("Set-Cookie"):
            for header in response.msg.get_all("Set-Cookie"):
                cookie = header.split(";", 1)[0]
                self._cookies.append(cookie)
        return super().parse_response(response)


# setup everything
DELAY_TIME = 0
FORUM_URL = "https://www.tapatalk.com/groups/berksforumvine/mobiquo/mobiquo.php"
transport = CookiesTransportHttps(context=ssl._create_unverified_context())
tt = xmlrpc.client.ServerProxy(FORUM_URL, transport=transport)
allMessages = []
doneIDs = []

# the single function to check a login
def login(username, password):
    global tt
    r = tt.login(username, password)
    loggedIn = r['result']
    return loggedIn


def getPms(username, password):
    global tt, allMessages
    result = {
        'status': False,
        'pms': []
    }
    l = login(username, password)
    if not l:
        print('login failed')
        return False

    getInbox(username, password)
    getSent(username, password)

    # sort by timestamp descending
    allMessages = sorted(allMessages, key=lambda k: k['timestamp'])
    for message in allMessages:
        print(str(message['timestamp']) + message['subject'])

    return allMessages


def getInbox(username, password):
    global tt, doneIDs, allMessages

    box = 0
    start = 0
    end = 20
    firstIdInChunk = -1

    # need to grab topics in 20 topic chunks
    continueGrabbingTopics = True
    while continueGrabbingTopics:

        # do this because TT is awful
        chunk = False
        while chunk == False:
            try:
                chunk = tt.get_box(str(box), start, end-1)
            except xmlrpc.client.ProtocolError:
                print("Yay, TT is awful")
                time.sleep(10)
                apiLogin()
                time.sleep(10)

        if 'result' in chunk and chunk['result'] == False:
            print("OH NO, Tapatalk error")
            print(chunk['result_text'].data)
            print(chunk['error'].data)
            sys.exit(0)

        chunk = chunk['list']

        if len(chunk) != 20 or firstIdInChunk == chunk[0]['msg_id']:
            # this is the last chunk
            continueGrabbingTopics = False

        if len(chunk) > 0:
            firstIdInChunk = chunk[0]['msg_id']

        for message in chunk:

            if int(message['msg_id']) in doneIDs:
                continue

            message2 = ttGetMessage(message['msg_id'], username, password)

            if 'result' in message2 and message2['result'] == False and message2['result_text'].data.decode('utf8') == 'Get message failed!':
                # ooh boy, this is an annoying error to deal with
                print("Can't get full message, using truncated one")
                message2 = message
                message2['text'] = message['short_content']

            msg = {
                'id': int(message['msg_id']),
                'top_id': -1,
                'from_id': -1,
                'from_name': message2['msg_from'].data.decode('utf8'),
                'timestamp': int(message2['timestamp']),
                'subject': message2['msg_subject'].data.decode('utf8'),
                'text': message2['text_body'].data.decode('utf8'),
                'to_id': -1,
                'to_name': username,
                'has_reply': False
            }
            allMessages.append(msg)
            doneIDs.append(int(message['msg_id']))
            print(len(allMessages))
            time.sleep(DELAY_TIME)

        start = start + 20
        end = end + 20
    #return messages


def getSent(username, password):
    global tt, doneIDs, allMessages

    box = -1
    start = 0
    end = 20
    firstIdInChunk = -1

    # need to grab topics in 20 topic chunks
    continueGrabbingTopics = True
    while continueGrabbingTopics:

        # do this because TT is awful
        chunk = False
        while chunk == False:
            try:
                chunk = tt.get_box(str(box), start, end-1)
            except xmlrpc.client.ProtocolError:
                print("Yay, TT is awful")
                time.sleep(10)
                apiLogin()
                time.sleep(10)

        if 'result' in chunk and chunk['result'] == False:
            print("OH NO, Tapatalk error")
            print(chunk['result_text'].data)
            print(chunk['error'].data)
            sys.exit(0)

        chunk = chunk['list']

        if len(chunk) != 20 or firstIdInChunk == chunk[0]['msg_id']:
            # this is the last chunk
            continueGrabbingTopics = False

        if len(chunk) > 0:
            firstIdInChunk = chunk[0]['msg_id']

        for message in chunk:

            if int(message['msg_id']) in doneIDs:
                continue

            message2 = ttGetMessage(message['msg_id'], username, password)

            if 'result' in message2 and message2['result'] == False and message2['result_text'].data.decode('utf8') == 'Get message failed!':
                # ooh boy, this is an annoying error to deal with
                print("Can't get full message, using truncated one")
                message2 = message
                message2['text'] = message['short_content']

            msg = {
                'id': int(message['msg_id']),
                'top_id': -1,
                'from_id': -1,
                'from_name': message2['msg_from'].data.decode('utf8'), # same here
                'timestamp': int(message2['timestamp']),
                'subject': message2['msg_subject'].data.decode('utf8'),
                'text': message2['text_body'].data.decode('utf8'),
                'to_id': -1,
                'to_name': message2['msg_to'][0]['username'].data.decode('utf8'),
                'has_reply': False
            }
            allMessages.append(msg)
            doneIDs.append(int(message['msg_id']))
            print(len(allMessages))
            time.sleep(DELAY_TIME)

        start = start + 20
        end = end + 20
    #return messages


def ttGetMessage(msg_id, username, password):
    # do this because TT is awful
    print("message = tt.get_message(" + str(msg_id) + ", " + str(0) + ", False)")
    message = tt.get_message(str(msg_id), str(0), False)
    return message
