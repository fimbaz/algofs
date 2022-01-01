import itertools
import re
from algosdk.future import transaction
from disas import program_scratch
from pyteal import *
from algosdk.future import transaction
from algosdk import encoding
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
class AppendAppTxn:
    def create(player):
        with open("append.teal") as f1,open("clear.teal") as f2:
            approval_program = player.algod.compile(f1.read())
            clear_program = player.algod.compile(f2.read())
        txn = transaction.ApplicationCreateTxn(
            player.hot_account,
            player.params,
            approval_program=base64.b64decode(approval_program),
            clear_program=base64.b64decode(clear_program),
            on_complete=transaction.OnComplete.NoOpOC,
            global_schema=transaction.StateSchema(num_uints=6, num_byte_slices=58),
            local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
        )
        return txn
    def append(player,data):
        txn = transaction.ApplicationCallTxn(player.hot_account,
                                             player.params,
                                             on_complete=transaction.OnComplete.NoOpOC,
                                             app_args=["append",data])
        return txn

def read_app(player, app_id):
    info = player.algod.application_info(app_id)
    global_state = info["params"]["global-state"]
    for item in global_state:
        item["key"]
        item["value"]
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
    program = open("append.teal","r").read()
    compiled_approval_program = player.algod.compile(
        program
    )["result"]
    compiled_clear_program = player.algod.compile(
        compileTeal(Return(Int(1)), Mode.Application)
    )["result"]
    how_dry_i_am = dryrun(player.algod,compiled_approval_program,compiled_clear_program,arglist=[["append","chips ahoy"],["append","chips ahoy m8"]],hot_account=player.hot_account)
    print({v['key']:base64.b64decode(v['value']['bytes']) for v in how_dry_i_am['txns'][2]['global-delta'] if 'bytes' in v['value']})
