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


MAX_GLOB_LEN = 120  # TODO get from consensus
MAX_SCRATCH_SLOTS = 64
# TODO save 7 bytes.

def load_bytes():
    # We're gonna leave this loop unrolled for now.
    seq = []
    for i in range(64,MAX_SCRATCH_SLOTS+64):
        seq.append(If(App.globalGetEx(Int(1),Itob(Int(i))).hasValue(),ScratchVar(TealType.bytes,slotId=i).store(App.globalGet(Itob(Int(i)))),Return(Int(1))))
    seq.append(Return(Int(1)))
    return Seq(seq)
    
@Subroutine(TealType.uint64)
def concat_bytes(arg):
    tail_index = ScratchVar(TealType.uint64)
    stub_space = ScratchVar(TealType.uint64)
    bytes_written = ScratchVar(TealType.uint64)
    bytes_to_write = ScratchVar(TealType.uint64)
    varisempty = ScratchVar(TealType.uint64)
    bytes_left = ScratchVar(TealType.uint64)
    # pyteal can't do variable existence inside loops because it breaks the scratch model,
    # that explains about half the 'style' below.  The other half is because i wrote it while
    # being beaten by children
    return Seq(
        [
            bytes_to_write.store(Int(0)),
            bytes_written.store(Int(0)),
            varisempty.store(Int(0)),
            tail_index.store(App.globalGet(Bytes("Tail")) / Int(MAX_GLOB_LEN)),
            stub_space.store(
                Int(MAX_GLOB_LEN) - (App.globalGet(Bytes("Tail")) % Int(MAX_GLOB_LEN))
            ),
            If(tail_index.load() == Int(0), App.globalPut(Itob(Int(0)), Bytes(""))),
            While(Len(arg) > bytes_written.load()).Do(
                Seq(
                    [
                        bytes_left.store(
                            Len(arg) - (bytes_written.load())
                        ),
                        bytes_to_write.store(
                            If(varisempty.load(), bytes_left.load(), stub_space.load())
                        ),
                        bytes_to_write.store(
                            If(
                                bytes_to_write.load() > Int(MAX_GLOB_LEN),
                                Int(MAX_GLOB_LEN),
                                bytes_to_write.load(),
                            )
                        ),
                        bytes_to_write.store(
                            If(
                                bytes_to_write.load() > bytes_left.load(),
                                bytes_left.load(),
                                bytes_to_write.load(),
                            )
                        ),
                        App.globalPut(
                            Itob(tail_index.load()),
                            Concat(
                                If(
                                    varisempty.load(),
                                    Bytes(""),
                                    App.globalGet(Itob(tail_index.load())),
                                ),
                                Extract(
                                    arg,
                                    bytes_written.load(),
                                    bytes_to_write.load(),
                                ),
                            ),
                        ),
                        tail_index.store(tail_index.load() + Int(1)),
                        bytes_written.store(
                            bytes_written.load() + bytes_to_write.load()
                        ),
                        varisempty.store(Int(1)),
                    ]
                )
            ),
            App.globalPut(
                Bytes("Tail"),
                App.globalGet(Bytes("Tail")) + bytes_written.load(),
            ),
            Return(bytes_written.load()),
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
        [Txn.application_args[0] == Bytes("append"), Seq([Return(concat_bytes(Txn.application_args[1]))])],
    )
    compiled_program = player.algod.compile(
        compileTeal(program, Mode.Application, version=5)
    )["result"]
    program = compileTeal(program, Mode.Application, version=5)
    import pdb
    pdb.set_trace()
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
        global_schema=transaction.StateSchema(num_uints=1, num_byte_slices=63),
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
        app_args=[
            "append",
            "I personally think alan greenspan is coolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcoolcooly.",
        ],
    )
    transaction.assign_group_id([txn1])
    stxn1 = player.wallet.sign_transaction(txn1)
    txid = player.algod.send_transactions([stxn1])
    txn1 = transaction.ApplicationCallTxn(
        player.hot_account,
        player.params,
        app_id,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=[
            "append",
            "I personally think alan greenspan is even nice smelling..............................................................................................................................",
        ],
    )
    transaction.assign_group_id([txn1])
    stxn1 = player.wallet.sign_transaction(txn1)
    txid = player.algod.send_transactions([stxn1])

    print(wait_for_confirmation(player.algod, txid), flush=True)
