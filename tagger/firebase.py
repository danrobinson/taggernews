# adapted from firebase/EventSource-Examples/python/chat.py by Shariq Hashme

from sseclient import SSEClient
import requests

import json
import threading
import socket


class ClosableSSEClient(SSEClient):

    def __init__(self, *args, **kwargs):
        self.should_connect = True
        super(ClosableSSEClient, self).__init__(*args, **kwargs)

    def _connect(self):
        if self.should_connect:
            super(ClosableSSEClient, self)._connect()
        else:
            raise StopIteration()

    def close(self):
        self.should_connect = False
        self.retry = 0
        try:
            self.resp.raw._fp.fp._sock.shutdown(socket.SHUT_RDWR)
            self.resp.raw._fp.fp._sock.close()
        except AttributeError:
            pass


class RemoteThread(threading.Thread):

    def __init__(self, parent, URL, function):
        self.function = function
        self.URL = URL
        self.parent = parent
        super(RemoteThread, self).__init__()

    def run(self):
        try:
            self.sse = ClosableSSEClient(self.URL)
            for msg in self.sse:
                msg_data = json.loads(msg.data)
                if msg_data is None:    # keep-alives
                    continue
                msg_event = msg.event
                # TODO: update parent cache here
                self.function((msg.event, msg_data))
        except socket.error:
            pass    # this can happen when we close the stream
        except KeyboardInterrupt:
            self.close()

    def close(self):
        if self.sse:
            self.sse.close()


def firebaseURL(URL):
    if '.firebaseio.com' not in URL.lower():
        if '.json' == URL[-5:]:
            URL = URL[:-5]
        if '/' in URL:
            if '/' == URL[-1]:
                URL = URL[:-1]
            URL = 'https://' + \
                URL.split('/')[0] + '.firebaseio.com/' + URL.split('/', 1)[1] + '.json'
        else:
            URL = 'https://' + URL + '.firebaseio.com/.json'
        return URL

    if 'http://' in URL:
        URL = URL.replace('http://', 'https://')
    if 'https://' not in URL:
        URL = 'https://' + URL
    if '.json' not in URL.lower():
        if '/' != URL[-1]:
            URL = URL + '/.json'
        else:
            URL = URL + '.json'
    return URL


class subscriber:

    def __init__(self, URL, function):
        self.cache = {}
        self.remote_thread = RemoteThread(self, firebaseURL(URL), function)

    def start(self):
        self.remote_thread.start()

    def stop(self):
        self.remote_thread.close()
        self.remote_thread.join()

    def wait(self):
        self.remote_thread.join()


class FirebaseException(Exception):
    pass


def put(URL, msg):
    to_post = json.dumps(msg)
    response = requests.put(firebaseURL(URL), data=to_post)
    if response.status_code != 200:
        raise FirebaseException(response.text)


def patch(URL, msg):
    to_post = json.dumps(msg)
    response = requests.patch(firebaseURL(URL), data=to_post)
    if response.status_code != 200:
        raise FirebaseException(response.text)


def get(URL):
    response = requests.get(firebaseURL(URL))
    if response.status_code != 200:
        raise FirebaseException(response.text)
    return json.loads(response.text)


def push(URL, msg):
    to_post = json.dumps(msg)
    response = requests.post(firebaseURL(URL), data=to_post)
    if response.status_code != 200:
        raise Exception(response.text)
