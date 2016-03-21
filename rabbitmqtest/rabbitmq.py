# coding: utf-8
import commands
import re
import requests

import pika

global ALL_MESSAGE
ALL_MESSAGE = ''
global PORT
PORT = ''


class RabbitMQInfo(object):
    def __init__(self, host='localhost', username='guest', password='guest'):
        host = host
        self.auth = (username, password)
        global PORT
        if not PORT:
            PORT = self._get_port()
        self.port = PORT
        self.url_suff = 'http://%s:%s/api' % (host, self.port)

    def _get_port(self):
        stat, output = commands.getstatusoutput('netstat -tnlp | grep 5672 | grep 0.0.0.0:*')
        if not stat:
            pattern = re.compile(r':(\d{5})\s')
            ports = pattern.findall(output)
        else:
            raise
        for port in ports:
            url = '%s/%s' % ('http://localhost:%s/api' % port, 'overview')
            try:
                r = requests.get(url, auth=self.auth, timeout=1)
            except requests.exceptions.ReadTimeout:
                continue
            if r.status_code == 200:
                return port

    def overview(self):
        url = '%s/%s' % (self.url_suff, 'overview')
        r = requests.get(url, auth=self.auth)
        return str2list(r.content)

    def channels(self):
        url = '%s/%s' % (self.url_suff, 'channels')
        r = requests.get(url, auth=self.auth)
        return str2list(r.content)

    def exchanges(self):
        url = '%s/%s' % (self.url_suff, 'exchanges')
        r = requests.get(url, auth=self.auth)
        return str2list(r.content)

    def queues(self):
        url = '%s/%s' % (self.url_suff, 'queues')
        r = requests.get(url, auth=self.auth)
        return str2list(r.content)

    def get_exchanges(self):
        exchanges = []
        for exchange in self.exchanges():
            name = exchange.get('name')
            if name:
                exchanges.append((name, name))
        return exchanges


class Message(object):
    def __init__(self, host='localhost'):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host))
        self.channel = self.connection.channel()

    def __del__(self):
        self.connection.close()

    def create_exchange(self, name='hello', type='direct'):
        self.channel.exchange_declare(exchange=name, type=type)

    def send(self, exchange, route, message):
        self.channel.basic_publish(exchange=exchange,
                                   routing_key=route,
                                   body=message)

    def add_custome(self, exchange=None, route=None):
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        for r in route:
            self.channel.queue_bind(exchange=exchange,
                                    queue=queue_name,
                                    routing_key=r)
        self.channel.basic_consume(callback,
                                   queue=queue_name,
                                   no_ack=True)
        self.channel.start_consuming()


def callback(ch, method, properties, body):
    # print dir(method)
    print method.consumer_tag
    body = 'exchange(%s),consumer_tag(%s): <em>%s</em><br/>' % (
        method.exchange, method.consumer_tag, body)
    global ALL_MESSAGE
    ALL_MESSAGE = ALL_MESSAGE + body


def str2list(s):
    return eval(s.replace('false', 'False').replace('true', 'True'))


def get_message():
    global ALL_MESSAGE
    return ALL_MESSAGE
