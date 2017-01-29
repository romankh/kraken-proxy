#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

import ZODB
import ZODB.FileStorage
import persistent
import socket
import transaction


class KrakenProxy(object):
    def __init__(self, database, port, kraken_host, kraken_port):
        self.host = "0.0.0.0"
        self.port = port
        self.kraken_host = kraken_host
        self.kraken_port = kraken_port

        db_storage = ZODB.FileStorage.FileStorage(database)
        db = ZODB.DB(db_storage)
        self.db_connection = db.open()
        self.requests = self.db_connection.root()

        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind((self.host, self.port))
        self.srv.listen(1)

        self.hits = 0
        self.miss = 0

    def run(self):
        print("Proxy listening on port %i" % self.port)
        print("%i entries in database." % len(self.requests))
        while True:
            try:
                conn, addr = self.srv.accept()
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    if data.startswith("crack"):
                        response = self.handle_request(data)
                        conn.send(response)

                conn.close()
            except KeyboardInterrupt:
                break

    def handle_request(self, msg):
        msg_xored_bits = msg.split(" ")[1]
        msg_xored_bits = msg_xored_bits.replace("\n", "")

        if self.requests.has_key(msg_xored_bits):
            request = self.requests[msg_xored_bits]
            self.hits += 1
        else:
            request = self.ask_kraken(msg)
            if request is not None:
                self.requests[request.get_bits()] = request
                transaction.commit()
                self.miss += 1

        if self.miss > 0 and self.hits > 0:
            print "hit rate %.2f (%i hits / %i miss / %i entries in DB)" % (
                self.hits / self.miss, self.hits, self.miss, len(self.requests))
        else:
            print "%i hits / %i miss / %i entries in DB" % (self.hits, self.miss, len(self.requests))

        return request.get_response()

    def ask_kraken(self, msg):
        sock = None
        all_responses = ""

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.kraken_host, self.kraken_port))
            sock.send(msg)
            while True:
                response = sock.recv(1024)
                if not response:
                    break
                else:
                    all_responses += response
                    if "crack #" in response:
                        break

            msg_xored_bits = msg.split(" ")[1].strip()
            return KrakenRequest(msg_xored_bits, all_responses)

        except KeyboardInterrupt:
            pass
        except socket.error as e:
            print e
        finally:
            if sock is not None:
                sock.close()
                sock = None

    def stop(self):
        self.db_connection.close()


class KrakenRequest(persistent.Persistent):
    def __init__(self, bits, response):
        self.bits = bits
        self.response = response

    def get_bits(self):
        return self.bits

    def get_response(self):
        return self.response


if __name__ == '__main__':
    proxy = KrakenProxy("db/kraken-requests.fs", 9999, "192.168.1.163", 4711)
    try:
        proxy.run()
    finally:
        proxy.stop()
