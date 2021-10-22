import algosdk
import os
import base64
from block2 import DataBlock
from pyteal import *
from algosdk.future import transaction
from util import Player, wait_for_confirmation


def clear_program(player):
    program = Return(Int(1))
    compiled_program = player.algod.compile(
        compileTeal(program, Mode.Application, version=4)
    )["result"]
    return compiled_program


def approval_program(player, return_int):
    program = Cond(
        [
            Txn.rekey_to() != Global.zero_address(),
            Return(Int(0)),
        ],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(1))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(1))],
        [Txn.application_id() == Int(0), Return(Int(1))],
        [Txn.application_args[0] == Bytes("info"), Return(Int(return_int))],
    )
    compiled_program = player.algod.compile(
        compileTeal(program, Mode.Application, version=4)
    )["result"]
    return compiled_program


# 1. create application
# in one txn:
# 2. update application
# 3. call application
# validate that the updated application is executed.. without this property
# we are pretty screwed.
if __name__ == "__main__":
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
    print("Creating...", flush=True)
    txn = transaction.ApplicationCreateTxn(
        player.hot_account,
        player.params,
        approval_program=base64.b64decode(approval_program(player, 0)),
        clear_program=base64.b64decode(clear_program(player)),
        on_complete=transaction.OnComplete.NoOpOC,
        global_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
    )
    signed_txn = player.wallet.sign_transaction(txn)
    txid = player.algod.send_transaction(signed_txn)
    print("sending..", flush=True)
    app_id = wait_for_confirmation(player.algod, txid)["application-index"]
    print(f"created {app_id}", flush=True)
    print("Update/call...", flush=True)
    txn1 = transaction.ApplicationUpdateTxn(
        player.hot_account,
        player.params,
        app_id,
        approval_program=base64.b64decode(approval_program(player, 1)),
        clear_program=base64.b64decode(clear_program(player)),
    )
    txn2 = transaction.ApplicationCallTxn(
        player.hot_account,
        player.params,
        app_id,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args = ["info"],
    )
    transaction.assign_group_id([txn1, txn2])
    stxn1 = player.wallet.sign_transaction(txn1)
    stxn2 = player.wallet.sign_transaction(txn2)
    txid = player.algod.send_transactions([stxn1, stxn2])
    print(wait_for_confirmation(player.algod, txid), flush=True)

