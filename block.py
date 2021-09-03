from algosdk.future import transaction
from disas import program_scratch
from pyteal import *
from algosdk.future import transaction
from algosdk import encoding
from util import wait_for_confirmation, application_state, big_endian, Player
from algosdk.v2client import algod
import base64
from docopt import docopt
class DataBlock(object):
    MAX_BLOCK_SIZE = 8000  # might have to play with this.

    def __init__(self, algod=None, app_id=None, data=None):
        if not (app_id or data) or (app_id and data):
            raise ValueError("specify either app_id or data")
        if data:
            program_data = DataBlock.compile_programs(
                algod, DataBlock.approval_program(data), DataBlock.clear_program()
            )
        else:
            program_data, data = DataBlock.load_programs(algod, app_id)
        DataBlock.initialize(self, algod, app_id, program_data, data)

    def initialize(self, algod, app_id, program_data, data):
        self.algod = algod
        self.app_id = app_id
        self.program_data = program_data
        self.data = data

    def burn(self, player):
        params = self.algod.suggested_params()
        params.fee = 1000
        params.flat_fee = True
        txn = transaction.ApplicationCreateTxn(
            player.hot_account,
            player.params,
            approval_program=base64.b64decode(self.program_data[0]),
            clear_program=base64.b64decode(self.program_data[1]),
            on_complete=transaction.OnComplete.NoOpOC,
            global_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
            local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
            extra_pages=3
        )
        signed_txn = player.wallet.sign_transaction(txn)
        self.txn_result = player.algod.send_transaction(signed_txn)
        confirmation = wait_for_confirmation(player.algod, self.txn_result)
        self.app_id = confirmation['application-index']
        return confirmation['application-index']
    
    def load_programs(algod, app_id):
        result = application_state(algod, app_id)
        program_data = (result["approvalProgram"], result["clearStateProgram"])
        data_array = program_scratch(algod, program_data[0], program_data[1] ,app_id,)
        return (program_data, b"".join([base64.b64decode(d)  for d in (data_array)]))

    def compile_programs(algod, approval_program, clear_program):
        compiled_approval_program = algod.compile(
            compileTeal(approval_program, Mode.Application, version=4)
        )["result"]

        compiled_clear_program = algod.compile(
            compileTeal(clear_program, Mode.Application)
        )["result"]
        return compiled_approval_program, compiled_clear_program

    def clear_program():
        program = Return(Int(1))
        return program

    def approval_program(data):
        if len(data) > DataBlock.MAX_BLOCK_SIZE:
            raise ValueError("payload is too large")

        data_code = [
            ScratchVar().store(Bytes(data[i : i + 32])) for i in range(0, len(data), 32)
        ]

        data_code_block = Seq((data_code + [Return(Int(1))]))

        program = Cond(
            [
                Txn.rekey_to() != Global.zero_address(),
                Return(Int(0)),
            ],
            [
                Or(
                    Txn.on_completion() == OnComplete.DeleteApplication,
                    Txn.on_completion() == OnComplete.UpdateApplication,
                ),
                Return(App.globalGet(Bytes("Owner")) == Txn.sender()),
            ],
            [Txn.application_id() == Int(0), Return(Int(1))],
            [Txn.application_args[0] == Bytes("info"), data_code_block],
            
        )
        return program


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
    block.py read <app-id>
    block.py write <file>
""")
    if args["read"]:
        block = DataBlock(
            algod=algod.AlgodClient(os.environ["ALGOD_TOKEN"], os.environ["ALGOD_URL"]),
            app_id=int(args["<app-id>"])
        )
        print(block.data.decode('utf-8'))
    elif args["write"]:
        block = DataBlock(
            algod=algod.AlgodClient(os.environ["ALGOD_TOKEN"], os.environ["ALGOD_URL"]),
            data=open(args["<file>"]).read()
        )
        block.burn(player)
        print(block.app_id)

