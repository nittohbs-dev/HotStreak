"""会場用のREST/WS接続。通信待ちはPygameスレッドから分離する。"""
import json
from queue import Empty, Queue
from threading import Event, Thread
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4
import websocket


class DisplayConnection:
    def __init__(self, server):
        self.server = server.rstrip('/')
        self.messages, self.commands = Queue(), Queue()
        self.stop = Event()
        self.sid = self.token = self.join_url = None
        self.thread = Thread(target=self.run, daemon=True)

    def request(self, path, body=None, key=None):
        headers = {'Accept': 'application/json'}
        if self.token:
            headers['X-Display-Token'] = self.token
        if key:
            headers['Idempotency-Key'] = key
        if body is not None:
            headers['Content-Type'] = 'application/json'
        request = Request(self.server+path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
        try:
            with urlopen(request, timeout=4) as response:
                return json.load(response)
        except HTTPError as error:
            try:
                message = json.load(error).get('message', '操作できません')
            except (ValueError, AttributeError):
                message = '操作できません'
            raise ValueError(message) from error

    def advance(self, snapshot, first_player=None):
        body = dict(phase=snapshot['phase'], revision=snapshot['revision'])
        if first_player and snapshot['phase'] == 'setup-cards':
            body['firstPlayerId'] = first_player
        self.commands.put((body, str(uuid4())))

    def run(self):
        while not self.stop.is_set():
            ws = None
            try:
                if self.sid is None:
                    created = self.request('/api/sessions', {})
                    self.sid, self.token, self.join_url = created['sessionId'], created['displayToken'], created['joinUrl']
                    self.messages.put(('session', dict(sessionId=self.sid, joinUrl=self.join_url)))
                path = f'/api/sessions/{self.sid}'
                ws = websocket.create_connection(self.server.replace('http', 'ws', 1)+f'/ws/sessions/{self.sid}', timeout=4)
                ws.settimeout(.15)
                self.messages.put(('state', self.request(path)))
                self.messages.put(('connected', {}))
                while not self.stop.is_set():
                    try:
                        body, key = self.commands.get_nowait()
                    except Empty:
                        pass
                    else:
                        try:
                            try:
                                result = self.request(path+'/advance', body, key)
                            except (OSError, URLError):
                                # 結果不明の要求は同じID・revisionで一度だけ再送する。
                                result = self.request(path+'/advance', body, key)
                            self.messages.put(('state', result))
                            self.messages.put(('ack', {}))
                        except ValueError as error:
                            self.messages.put(('error', {'message': str(error)}))
                            self.messages.put(('state', self.request(path)))
                    try:
                        raw = ws.recv()
                        if not raw:
                            raise ConnectionError('closed')
                        event = json.loads(raw)
                        if isinstance(event.get('payload'), dict):
                            self.messages.put(('state', event['payload']))
                    except websocket.WebSocketTimeoutException:
                        pass
            except (OSError, URLError, ValueError, websocket.WebSocketException) as error:
                self.messages.put(('disconnected', {'message': f'再接続しています… {error}'}))
            finally:
                if ws:
                    ws.close()
                while not self.commands.empty():
                    try:
                        self.commands.get_nowait()
                    except Empty:
                        break
                self.stop.wait(1)

    def close(self):
        self.stop.set()
        self.thread.join(timeout=5)
