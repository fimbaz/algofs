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
def dryrun_call(self, drr, **kwargs):
    data = json.dumps(drr).encode()
    req = "/teal/dryrun"
    headers = {"Content-Type": "application/msgpack"}
    kwargs["headers"] = headers
    return self.algod_request("POST", req, data=data, **kwargs)

def dryrun(algod, approval_program, clear_program, args=[],app_id=None,hot_account=None):
    args = [base64.b64encode(arg.encode("utf-8")).decode("utf-8") for arg in args]
    hot_account = hot_account
    data = dryrun_call(
        algod,
        drr={
            "accounts": [
                {
                    "address": hot_account if hot_account else "VCZCQGZ3BOKZQPE6J3QWRJPPEV4RFH2QK4SN7WP377RX447B3PKU4GM6XQ",
                    "amount": 1000000000,
                    "amount-without-pending-rewards": 1000000000,
                    "created-apps": [
                        {
                            "id": app_id if app_id else 1000000001,
                            "params": {
                                "approval-program": approval_program,
                                "clear-state-program": clear_program,
                                "creator": hot_account,
                                "global-state-schema": {
                                    "num-byte-slice": 63,
                                    "num-uint": 1,
                                },
                            },
                        }
                    ],
                    "round": 1,
                    "status": "Online",
                }
            ],
            "apps": [
                {
                    "id": app_id if app_id else 1000000001 ,
                    "params": {
                        "approval-program": approval_program,
                        "clear-state-program": clear_program,
                        "creator": hot_account,
                        "global-state-schema": {"num-byte-slice": 63, "num-uint": 1},
                    },
                }
            ],
            "latest-timestamp": 1,
            "round": 1,
            "sources": None,
            
            "txns": [
                {
                    "txn": {
                        "snd":hot_account,
                        "apaa": args,
                        "apid": app_id if app_id else 1000000001,
                        "fee": 1000,
                        "fv": 1,
                        "type": "appl",
                    }
                }
            ],
        },
    )
    return data


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
    how_dry_i_am = dryrun(player.algod,compiled_approval_program,compiled_clear_program,args=["append","chips ahoy"],hot_account=player.hot_account)
    print({v['key']:base64.b64decode(v['value']['bytes']) for v in how_dry_i_am['txns'][0]['global-delta'] if 'bytes' in v['value']})
