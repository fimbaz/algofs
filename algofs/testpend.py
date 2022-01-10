import random
import secrets
import itertools
import re
from algosdk.future import transaction
from disas import program_scratch
import pyteal
from algosdk.future import transaction
import algosdk
from util import (
    wait_for_confirmation,
    application_state,
    big_endian,
    Player,
    flatten,
    btoi,
    itob,
    compress_ranges,
)
from collections import deque
from algosdk.v2client import algod as algodclient
import base64
from docopt import docopt
import sys
import time
import json
import operator


def process_txn(player, txn, sync=False, sign=True, send=True):
    txn_result = None
    while True:
        player.params.first = player.algod.ledger_supply()["current_round"]
        player.params.last = player.params.first + 100
        if type(txn) == list:
            gid = transaction.calculate_group_id(txn)
            for t in txn:
                t.group = gid
        else:
            txn = [txn]
        if not sign:
            return txn
        signed_txn = [player.wallet.sign_transaction(t) for t in txn]
        if not send:
            return signed_txn
        try:
            if len(signed_txn) > 1:
                txn_result = player.algod.send_transactions(signed_txn)
            else:
                txn_result = player.algod.send_transaction(signed_txn[0])
            break
        except algosdk.error.AlgodHTTPError as e:
            message = json.loads(str(e))["message"]
            print("retry", file=sys.stderr)
            print(message)
            if "TransactionPool.Remember: fee" in message or "txn dead" in message:
                gevent.sleep(4)
            else:
                raise e
    if sync:
        return wait_for_confirmation(player.algod, txn_result)
    return txn_result


class AppendApp:
    def read(self):
        return read_app(self.player,self.app_id)
    def __init__(
        self,
        player,
        app_id=None,
        data="",
    ):
        self.player = player
        self.txns = []
        self.data = data
        if not app_id:
            self.app_id = process_txn(
                player, AppendAppTxn.create(player, data), sync=True
            )["application-index"]
        else:
            self.app_id = app_id
            self.data = read_app(player,self.app_id)
            
    def send(self, sync=True):
        groups = (self.txns[i : i + 16] for i in range(0, len(self.txns), 16))
        for group in groups:
            print(f"send {len(group)} txns")
            result = process_txn(self.player, group, sync=True)
        self.txns = []
        return result

    def append(self, data):
        if len(data) > 1000:
            for x in range(0, len(data), 1000):
                self.txns.append(
                    AppendAppTxn.append(player, self.app_id, data[x : x + 1000])
                )
        self.data = data
    def copy(self, app2):
        self.txns += [
            AppendAppTxn.copy(self.player, self.app_id, app2, 3)
            for i in range(0, (len(self.data) // (128 * 4)) + 2)
        ]

class AppendAppTxn:
    def creator():
        return AppendAppTxn.create

    def create(player, data):
        with open("algofs.teal") as f1:
            compiled_approval_program = player.algod.compile(f1.read())["result"]
        compiled_clear_program = player.algod.compile(
            pyteal.compileTeal(pyteal.Return(pyteal.Int(1)), pyteal.Mode.Application)
        )["result"]
        txn = transaction.ApplicationCreateTxn(
            player.hot_account,
            player.params,
            app_args=["append", data],
            approval_program=base64.b64decode(compiled_approval_program),
            clear_program=base64.b64decode(compiled_clear_program),
            on_complete=transaction.OnComplete.NoOpOC,
            global_schema=transaction.StateSchema(num_uints=6, num_byte_slices=58),
            local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
            lease=secrets.token_bytes(32),
        )
        return txn

    def append(player, app_id, data):
        txn = transaction.ApplicationCallTxn(
            player.hot_account,
            player.params,
            app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=["append", data],
        )
        return txn

    def copy(player, app_id1, app_id2, cycles):
        txn = transaction.ApplicationCallTxn(
            player.hot_account,
            player.params,
            app_id2,
            on_complete=transaction.OnComplete.NoOpOC,
            foreign_apps=[app_id1],
            lease=secrets.token_bytes(32),
            app_args=["copy", int(cycles)],
        )
        return txn


def read_app(player, app_id):
    info = player.algod.application_info(app_id)
    global_state = info["params"]["global-state"]
    literal_dict = []
    for item in global_state:
        base64.b64decode(item["key"])
        if item["value"]["type"] == 1:
            literal_dict.append(
                (
                    base64.b64decode(item["key"]),
                    base64.b64decode(item["value"]["bytes"]),
                )
            )
    return "".join(
        map(lambda x: x[1].decode("utf-8"), sorted(literal_dict))
    )  # ,key=lambda x: ord(x[0]))))


def test(player):
    data = " ".join([str(x) for x in range(1, 1000)])
    app = AppendApp(player)
    app2 = AppendApp(player)
    app.append(data)
    app.copy(app2.app_id)
    print(len(app.txns))
    print(app.send(sync=True))
    assert(app2.read()==app.read())
if __name__ == "__main__":
    import os

    player = Player(
        hot_account=os.environ["HOT_WALLET_KEY"],
        algod_url=os.environ["ALGOD_URL"],
        kmd_url=os.environ["KMD_URL"],
        indexer_url=os.environ["INDEXER_URL"],
        algod_token=os.environ["ALGOD_TOKEN"],
        kmd_token=os.environ["KMD_TOKEN"],
        indexer_token=os.environ["INDEXER_TOKEN"],
        wallet_name=os.environ["WALLET_NAME"],
        wallet_password=os.environ["WALLET_PASSWORD"],
    )
    args = docopt(
        """Usage:
    append.py test
    append.py read <app-id>
    append.py create <data>
    append.py append <data>
    append.py copy <source-app> <dest-app> <cycles>
        """
    )
    if args["test"]:
        test(player)
    elif args["read"]:
        print(read_app(player, int(args["<app-id>"])))
    elif args["create"]:
        data = args["<data>"]
        app_id = process_txn(
            player, AppendAppTxn.create(player, data[0:999]), sync=True
        )["application-index"]
        print(app_id)
    elif args["append"]:
        data = args["<data>"]
        if len(data) > 7000:
            raise "Input too large"
        txns = []
        for x in range(0, len(data), 1000):
            txns.append(AppendAppTxn.append(player, app_id, data[x : x + 1000]))
        print(process_txn(player, txns, sync=True))
        print(app_id)
    elif args["copy"]:
        source = int(args["<source-app>"])
        dest = int(args["<dest-app>"])
        cycles = int(args["<cycles>"])
        print(process_txn(player,AppendAppTxn.copy(player,source,dest,cycles),sync=True))
#        app1 = AppendApp(source)
#        app2 = AppendApp(dest)
#        app1.copy(app2.app_id)
