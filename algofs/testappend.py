import algosdk
import os
import base64
from block2 import DataBlock
from pyteal import *
from algosdk.future import transaction
from util import Player, wait_for_confirmation
from algosdk import account, encoding


def clear_program(player):
    program = Return(Int(1))
    compiled_program = player.algod.compile(
        compileTeal(program, Mode.Application, version=4)
    )["result"]
    return compiled_program


@Subroutine(TealType.uint64)
def get_tail():  # returns key index and offset
    i = ScratchVar(TealType.uint64)
    return Seq(
        [
            i.store(Int(0)),
            While(Itob(App.globalGet(Itob(i.load()))) != Itob(Int(0))).Do(
                i.store(i.load() + Int(1))
            ),
            Return(i.load()),
        ]
    )


MAX_GLOB_LEN = 256  # TODO get from consensus


@Subroutine(TealType.uint64)
def concat_bytes():
    tail_index = ScratchVar(TealType.uint64)
    tail = ScratchVar(TealType.bytes)
    stub_space = ScratchVar(TealType.uint64)
    bytes_read = ScratchVar(TealType.uint64)
    return Seq(
        [
            tail_index.store(App.globalGet(Bytes("Tail")) / Int(MAX_GLOB_LEN)),
            stub_space.store(App.globalGet(Bytes("Tail")) % Int(MAX_GLOB_LEN)),
            If(stub_space.load() == Int(0),stub_space.store(Int(MAX_GLOB_LEN))),
            App.globalPut(Itob(tail_index.load()), Bytes("")),
            tail.store(App.globalGet(Itob(tail_index.load()))),
            If(
                stub_space.load() > Len(Txn.application_args[1]) - Int(1),
                stub_space.store(Len(Txn.application_args[1]) - Int(1)),
            ),
            App.globalPut(
                Itob(tail_index.load()),
                Concat(
                    tail.load(),
                    Substring(
                        Txn.application_args[1], Int(0), stub_space.load()
                    ),
                ),
            ),
            bytes_read.store(stub_space.load()),
            While(
                Seq(
                    [
                        tail_index.store(tail_index.load() + Int(1)),
                        Len(Txn.application_args[1]) > bytes_read.load(),
                    ]
                )
            ).Do(
                Seq(
                    [
                        App.globalPut(
                            Itob(tail_index.load()),
                            Substring(
                                Txn.application_args[1],
                                Int(0),
                                bytes_read.load()
                            ),
                        ),
                        bytes_read.store(
                            bytes_read.load()
                            + If(
                                Len(Txn.application_args[1]) < Int(MAX_GLOB_LEN),
                                Len(Txn.application_args[1]),
                                Int(MAX_GLOB_LEN),
                            )
                        ),
                    ]
                )
            ),
            App.globalPut(Bytes("Tail"), tail_index.load() * Int(MAX_GLOB_LEN) + bytes_read.load()),
            Return(bytes_read.load()),
        ]
    )


def approval_program(player, return_int):
    program = Cond(
        [
            Txn.rekey_to() != Global.zero_address(),
            Return(Int(0)),
        ],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(1))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(1))],
        [Txn.application_id() == Int(0), Return(Int(1))],
        [Txn.application_args[0] == Bytes("append"), Seq([Return(concat_bytes())])],
    )
    compiled_program = player.algod.compile(
        compileTeal(program, Mode.Application, version=5)
    )["result"]
    return compiled_program


# 1. create application
# in one txn:
# 2. update application
# 3. call application
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
        global_schema=transaction.StateSchema(num_uints=1, num_byte_slices=10),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
    )
    signed_txn = player.wallet.sign_transaction(txn)
    txid = player.algod.send_transaction(signed_txn)
    print("sending..", flush=True)
    app_id = wait_for_confirmation(player.algod, txid)["application-index"]
    print(f"created {app_id}", flush=True)
    print("Update/call...", flush=True)
    txn1 = transaction.ApplicationCallTxn(
        player.hot_account,
        player.params,
        app_id,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=["append", "I personally think alan greenspan is cool."],
    )
    transaction.assign_group_id([txn1])
    stxn1 = player.wallet.sign_transaction(txn1)
    txid = player.algod.send_transactions([stxn1])
    txn1 = transaction.ApplicationCallTxn(
        player.hot_account,
        player.params,
        app_id,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=["append", "I personally think alan greenspan is even nice smelling."],
    )
    transaction.assign_group_id([txn1])
    stxn1 = player.wallet.sign_transaction(txn1)
    txid = player.algod.send_transactions([stxn1])

    print(wait_for_confirmation(player.algod, txid), flush=True)
