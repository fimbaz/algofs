import itertools
import re
from algosdk.future import transaction
from disas import program_scratch
import pyteal
from algosdk.future import transaction
#from algosdk import encodingfrom 
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
        with open("append.teal") as f1:
            compiled_approval_program = player.algod.compile(f1.read())
        compiled_clear_program = player.algod.compile(
            pyteal.compileTeal(pyteal.Return(pyteal.Int(1)), pyteal.Mode.Application)
        )["result"]

        txn = transaction.ApplicationCreateTxn(

 player.hot_account,
            player.params,
            approval_program=base64.b64decode(compiled_approval_program),
            clear_program=base64.b64decode(compiled_clear_program),
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
    literal_dict=[]
    for item in global_state:
        base64.b64decode(item["key"])
        if item["value"]["type"] == 1:
            literal_dict.append((base64.b64decode(item["key"]), base64.b64decode(item["value"]["bytes"])))
    return "".join(map(lambda x: x[1].decode('utf-8'),sorted(literal_dict))) #,key=lambda x: ord(x[0]))))

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
        """)
    print(read_app(player, int(args["<app-id>"])))
    
