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
from itertools import count


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


class AppendAppTxn:
    def creator():
        return AppendAppTxn.create

    def create(player, data):
        with open("append.teal") as f1:
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
    append.py read <app-id>
    append.py create <data>
        """
    )
    if args["read"]:
        print(read_app(player, int(args["<app-id>"])))
    elif args["create"]:
        data = args["<data>"]
        app_id = process_txn(player, AppendAppTxn.create(player, data[0:999]),sync=True)['application-index']
        if len(data) > 7000:
            raise "Input too large"
        txns = []
        if len(data) > 1000:
            for x in range(999, len(data), 1000):
                txns.append(AppendAppTxn.append(player, app_id, data[x : x + 1000]))
        print(process_txn(player, txns,sync=True))
        print(app_id)
