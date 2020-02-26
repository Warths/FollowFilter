import socket
import time
import threading
import datetime
from network.irc.event import Message
import utils.log as log
import traceback


class Irc:
    def __init__(self, nickname, oauth_key, channel, host='irc.chat.twitch.tv', port=6667):
        self.func_map = {}
        self.socket = None
        self.buffer = b''
        self.messages = []
        self.host = host
        self.oauth_key = oauth_key
        self.port = port
        self.nickname = nickname
        self.channel = channel
        self.last_ping = 300
        self.message = []
        self.started = False


        thread = threading.Thread(target=self.main_thread, args=())
        thread.daemon = True
        thread.start()

        ping_thread = threading.Thread(target=self.ping_thread, args=())
        ping_thread.daemon = True
        ping_thread.start()

        log.notice("Bot in %s starting. 3.." % self.channel)


    def open_socket(self, nickname, oauth_key, channel, host='irc.chat.twitch.tv', port=6667):
        self.started = False
        s = socket.socket()
        s.connect((host, port))
        s.send(("PASS " + oauth_key + "\r\n").encode("utf-8"))
        s.send(("NICK " + nickname + "\r\n").encode("utf-8"))
        s.send(("JOIN #" + channel + "\r\n").encode("utf-8"))
        s.send("CAP REQ :twitch.tv/membership\r\n".encode("utf-8"))
        s.send("CAP REQ :twitch.tv/commands\r\n".encode("utf-8"))
        s.send("CAP REQ :twitch.tv/tags\r\n".encode("utf-8"))
        self.last_ping = 300
        return s

    def init_room(self):
        loading = True
        while loading:
            self.buffer = self.buffer + self.socket.recv(1024)
            temp = self.buffer.split(b'\r\n')
            self.buffer = temp.pop()
            for line in temp:
                loading = self.loading_complete(str(line))
                if not loading:
                    break

    def loading_complete(self, packet):
        if 'End of /NAMES list' in packet:
            self.started = True
            return False
        else:
            return True

    def receive_data(self):
        self.buffer = self.buffer + self.socket.recv(1024)
        temp = self.buffer.split(b'\r\n')
        self.buffer = temp.pop()
        for message in temp:
            if message.decode('UTF-8') == 'PING :tmi.twitch.tv':
                self.socket.send('PONG :tmi.twitch.tv\r\n'.encode("UTF-8"))
                self.last_ping = 300
            elif self.started:
                self.messages.append(Message(message.decode('UTF-8'), self.channel))

    def get_message(self):
        messages = self.messages
        self.messages = []
        return messages

    def onEvent(self, name):
        def func_wrapper(func):
            self.func_map[name] = func
            return func
        return func_wrapper

    def call_registered(self, name=None, event=None):
        func = self.func_map.get(name, None)
        if func is None:
            return func
        return func(event)


    def send_message(self, message):
        message_temp = 'PRIVMSG #' + self.channel + ' :' + message
        self.socket.send((message_temp + "\r\n").encode("utf-8"))
        log.discrete("IRC : >> %s" % message_temp)

    def switch_channel(self, channel):
        self.socket.send(("PART #" + self.channel + "\r\n").encode("utf-8"))
        self.socket.send(("JOIN #" + channel + "\r\n").encode("utf-8"))
        self.channel = channel

    def connect_bot(self):
        while True:
                try:
                    self.socket = self.open_socket(self.nickname, self.oauth_key, self.channel, self.host, self.port)
                    self.socket.settimeout(300)
                    self.init_room()
                    return
                except (socket.timeout, socket.gaierror):
                    print('Could not reconnect.. Retrying in 5 seconds..')
                    time.sleep(4)


    def main_thread(self):
        self.connect_bot()
        while True:
            time.sleep(0.05)
            try:
                self.receive_data()
                for message in self.get_message():
                    self.call_registered('any', message)
                    self.call_registered(message.type, message)
            except Exception as error:
                log.warning('Error in IRC')
                log.warning(error)
                traceback.print_exc()
                self.connect_bot()



    def ping_thread(self):
        while True:
            self.last_ping = 300
            while self.last_ping >= 0:
                time.sleep(1)
                if self.last_ping <= 0:
                    print('Did not received ping since a long time .. ? ')
                    self.socket = None
                self.last_ping -= 1
