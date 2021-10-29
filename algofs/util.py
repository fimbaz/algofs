import gevent
from gevent import monkey

monkey.patch_all()
import json
import hashlib
from algosdk.wallet import Wallet
from docopt import docopt
from algosdk import account, encoding
from algosdk.error import AlgodHTTPError
from algosdk.kmd import KMDClient
from algosdk.error import KMDHTTPError
from algosdk.future.transaction import *
from algosdk.v2client import algod
from algosdk.wallet import Wallet
from algosdk.v2client import indexer
import os
import json
from docopt import docopt
import sys
import base64
import sys

from typing import Iterable

# from collections import Iterable
# < py38


def flatten(items):
    """Yield items from any nested iterable; see Reference."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


def wait_for_confirmation(client, txid):
    last_round = client.status().get("last-round")
    txinfo = {}
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        txinfo = client.pending_transaction_info(txid)
        gevent.sleep(10)
    return txinfo


def application_state(algodclient, app_id):
    try:
        appinfo = algodclient.application_info(app_id)
    except AlgodHTTPError as e:
        if json.loads(str(e))["message"] == "application does not exist":
            return {}
    keys = {
        base64.b64decode(item["key"]): base64.b64decode(item["value"]["bytes"])
        if item["value"]["type"] == 1
        else item["value"]["uint"]
        for item in (
            appinfo["params"]["global-state"]
            if "global-state" in appinfo["params"]
            else []
        )
    }
    out = {}
    for k, v in keys.items():
        try:
            out[k.decode("utf-8")] = encoding.encode_address(v)
        except TypeError:
            out[k.decode("utf-8")] = v
    out["approvalProgram"] = appinfo["params"]["approval-program"]
    out["clearStateProgram"] = appinfo["params"]["clear-state-program"]

    return out


import socket


def big_endian(integer):
    return socket.htonl(integer)


def itob(i):
    return bytes(
        [
            k & 255
            for k in [i >> 56, i >> 48, i >> 40, i >> 32, i >> 24, i >> 16, i >> 8, i]
        ]
    )


def itob16(i):
    return bytes([k & 255 for k in [i >> 8, i]])


def itob32(i):
    return bytes([k & 255 for k in [i >> 24, i >> 16, i >> 8, i]])


def btoi32(b):
    return (b[0] * 2 ** 24) + (b[1] * 2 ** 16) + (b[2] * 2 ** 8) + (b[3])


def btoi16(b):
    return (b[0] * 2 ** 8) + (b[1])


def btoi(b):
    return (
        (b[0] * 2 ** 56)
        + (b[1] * 2 ** 48)
        + (b[2] * 2 ** 40)
        + (b[3] * 2 ** 32)
        + (b[4] * 2 ** 24)
        + (b[5] * 2 ** 16)
        + (b[6] * 2 ** 8)
        + b[7]
    )


class Player(object):
    def __init__(
        self,
        hot_account,
        algod_url="http://127.0.0.1:4001",
        kmd_url="http://127.0.0.1:4002",
        indexer_url="http://127.0.0.1:8091",
        algod_token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        kmd_token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        indexer_token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        wallet_name="unencrypted-default-wallet",
        wallet_password="",
    ):
        self.hot_account = hot_account
        self.kmd = KMDClient(kmd_token, kmd_url)
        self.indexer = indexer.IndexerClient(indexer_token, indexer_url)
        self.algod = algod.AlgodClient(algod_token, algod_url)
        self.params = self.algod.suggested_params()
        self.params.last = self.algod.ledger_supply()["current_round"] + 100
        self.wallet = Wallet(wallet_name, wallet_password, self.kmd)
        self.params.fee = 1000
        self.params.flat_fee = True


def compress_ranges(sorted_list_of_ints_iter):
    head = next(sorted_list_of_ints_iter)
    tail = head
    for integer in sorted_list_of_ints_iter:
        if integer == tail + 1:
            tail = integer
        else:
            yield (head,tail)
            head = integer
            tail = integer
            

    
