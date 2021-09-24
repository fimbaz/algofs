from algosdk.future import transaction
from disas import program_scratch
from pyteal import *
from algosdk.future import transaction
from algosdk import encoding
import algosdk
from util import wait_for_confirmation, application_state, big_endian, Player, flatten
from algosdk.v2client import algod
import base64
from docopt import docopt
import sys
import time
import json
import operator

# 1. a block is read from the stream
# 2. an account is found for the block to live in
# 3. if necessary, an account funding txn is created and signed 
# 4. an applicationcreate txn is created and signed
# input: 64 bit unsigned integer
# output: 8 byte big-endian representation of same


# it takes a lot of engineering discipline not to fix these two functions.
def itob(i):
    return bytes(
        [
            k & 255
            for k in [i >> 56, i >> 48, i >> 40, i >> 32, i >> 24, i >> 16, i >> 8, i]
        ]
    )


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


class DataBlock(object):
    MAX_BLOCK_SIZE = 7000  # 1024 * 7  # might have to play with this.
    BLOCK_ACCOUNT_DEPOSIT = 9800000
    MAX_APPS_PER_ACCOUNT = 10
    BLOCK_TYPE_DATA = 1
    BLOCK_TYPE_INDEX = 2
    BLOCK_TYPE_FILE = 3
    BLOCK_TYPE_DIRECTORY = 4

    def create_accounts_for_data(wallet, size):
        block_count = size / DataBlock.MAX_BLOCK_SIZE
        accounts_needed = int(block_count / 10) + 1
        keys = wallet.list_keys()
        infos = [algod.account_info(key) for key in keys]
        accounts = {}
        for info in infos:
            if len(info["created-apps"]) > 0:
                next
            elif info["amount"] >= DataBlock.BLOCK_ACCOUNT_DEPOSIT:
                accounts[info["address"]] = 0
            else:
                accounts[info["address"]] = (
                    DataBlock.BLOCK_ACCOUNT_DEPOSIT - info["amount"]
                )

        accounts.update(
            {
                wallet.generate_key(): DataBlock.BLOCK_ACCOUNT_DEPOSIT
                for i in range(0, accounts_needed - len(accounts.keys()))
            }
        )
        return dict(list(accounts.items())[0:accounts_needed])

    def delete_everything(player):
        apps = []
        for key in player.wallet.list_keys():
            info = player.algod.account_info(key)
            apps += [app["id"] for app in info["created-apps"]]
        print(f"Delete {len(apps)} applications")
        DataBlock.delete_applications(player, apps)

    def delete_applications(player, app_ids):
        apps_by_account = {}
        for app_id in app_ids:
            try:
                info = player.algod.application_info(int(app_id))
                if info["params"]["creator"] not in apps_by_account.keys():
                    apps_by_account[info["params"]["creator"]] = []
                apps_by_account[info["params"]["creator"]] += [app_id]
            except algosdk.error.AlgodHTTPError as e:
                if json.loads(str(e))["message"] == "application does not exist":
                    continue
        txns = []
        for account, apps in apps_by_account.items():
            txns += [
                player.wallet.sign_transaction(
                    transaction.ApplicationDeleteTxn(account, player.params, app)
                )
                for app in apps
            ]
        print(f"Deleting {len(txns)} apps", file=sys.stderr)
        txids = []
        for txn in txns:
            try:
                txids.append(player.algod.send_transaction(txn))
            except algosdk.error.AlgodHTTPError:
                continue

        _ = [wait_for_confirmation(player.algod, txid) for txid in txids]
        return txids

    def allocate_space(player, length):
        accounts_and_balances = DataBlock.create_accounts_for_data(
            player.wallet, len(data)
        )
        print(
            f"found {len(accounts_and_balances)} accounts requiring {len(accounts_and_balances)*DataBlock.BLOCK_ACCOUNT_DEPOSIT/1000000} ALGO to hold {int(len(data)/1024)} KB. Funding with {sum(accounts_and_balances.values())/1000000} ALGO",
            file=sys.stderr,
        )
        DataBlock.fund_accounts(player, accounts_and_balances)
        return accounts_and_balances

    def big_burn(player, data):
        accounts_and_balances = DataBlock.allocate_space(player, len(data))
        blocks = DataBlock.data_to_blocks(player.algod, data)
        txid_groups = []
        accounts = list(accounts_and_balances.keys())
        for account_i, block_group in enumerate(
            [
                blocks[i : i + DataBlock.MAX_APPS_PER_ACCOUNT]
                for i in range(0, len(blocks), DataBlock.MAX_APPS_PER_ACCOUNT)
            ]
        ):
            txid_groups += [
                [accounts[account_i]]
                + [block.burn(player, accounts[account_i]) for block in block_group]
            ]
        application_ids = [
            [txid_group[0]]
            + [
                wait_for_confirmation(player.algod, txid)["application-index"]
                for txid in txid_group[1:]
            ]
            for txid_group in txid_groups
        ]
        return application_ids

    def fund_accounts(player, accounts):
        txns = [
            player.wallet.sign_transaction(
                transaction.PaymentTxn(
                    player.hot_account, player.params, account, amount
                )
            )
            for account, amount in accounts.items()
            if amount > 0
        ]
        txids = [player.algod.send_transaction(t) for t in txns]
        _ = [wait_for_confirmation(algod, txid) for txid in txids]
        return txids

    def data_to_blocks(algod, data):
        blocks = []
        for block, position in enumerate(range(0, len(data), DataBlock.MAX_BLOCK_SIZE)):
            if block % 100 == 0:
                print(".", file=sys.stderr)
            blocks.append(
                DataBlock(
                    algod,
                    block_type=DataBlock.BLOCK_TYPE_DATA,
                    data=data[position : position + DataBlock.MAX_BLOCK_SIZE],
                )
            )
        return blocks

    def __init__(self, algod=None, block_type=0, app_id=None, data=None, sync=False):
        if not (app_id or data) or (app_id and data):
            raise ValueError("specify either app_id or data")
        if data:
            program_data = DataBlock.compile_programs(
                algod,
                DataBlock.approval_program(data, block_type),
                DataBlock.clear_program(),
            )
        else:
            (program_data, data, block_type) = DataBlock.load_programs(algod, app_id)
        DataBlock.initialize(self, algod, app_id, program_data, data, block_type)

    def initialize(self, algod, app_id, program_data, data, block_type):
        self.algod = algod
        self.program_data = program_data
        self.data = data
        self.block_type = block_type
        self.app_id = app_id

    def burn(self, player, account=None, sync=False):
        params = self.algod.suggested_params()
        params.fee = 1000
        params.flat_fee = True
        txn = transaction.ApplicationCreateTxn(
            player.hot_account if not account else account,
            player.params,
            approval_program=base64.b64decode(self.program_data[0]),
            clear_program=base64.b64decode(self.program_data[1]),
            on_complete=transaction.OnComplete.NoOpOC,
            global_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
            local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
            extra_pages=3,
        )
        signed_txn = player.wallet.sign_transaction(txn)
        while True:
            try:
                self.txn_result = player.algod.send_transaction(signed_txn)
                break
            except algosdk.error.AlgodHTTPError as e:
                print("retry", file=sys.stderr)
                if (
                    "TransactionPool.Remember: fee {1000}"
                    in json.loads(str(e))["message"]
                ):
                    time.sleep(5)
                    continue
                else:
                    raise e
        if sync:
            self.app_id = wait_for_confirmation(player.algod, self.txn_result)[
                "application-index"
            ]
            print(self.app_id)
        self.txid = self.txn_result
        return self.txn_result

    def load_programs(algod, app_id):
        result = application_state(algod, app_id)
        program_data = (result["approvalProgram"], result["clearStateProgram"])
        data_array = program_scratch(
            algod,
            program_data[0],
            program_data[1],
            app_id,
        )
        block_type = data_array[0]
        data = b"".join([base64.b64decode(d) for d in (data_array[1:])])
        return (program_data, data, block_type)

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

    def approval_program(data, block_type=1):
        if len(data) > DataBlock.MAX_BLOCK_SIZE:
            raise ValueError("payload is too large")

        data_code = [ScratchVar().store(Int(block_type))] + [
            ScratchVar().store(
                Bytes("base64", base64.b64encode(data[i : i + 32]).decode("utf-8"))
            )
            for i in range(0, len(data), 32)
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
                Return(Global.creator_address() == Txn.sender()),
            ],
            [Txn.application_id() == Int(0), Return(Int(1))],
            [Txn.application_args[0] == Bytes("info"), data_code_block],
        )
        return program


class IndexBlock(object):
    def index_datablocks(player, blocks):
        out = b""
        data = b"".join([itob(block.app_id) for block in blocks])
        return [
            DataBlock(
                algod,
                block_type=DataBlock.BLOCK_TYPE_INDEX,
                data=data[position : position + DataBlock.MAX_BLOCK_SIZE],
            )
            for position in range(0, len(data), DataBlock.MAX_BLOCK_SIZE)
        ]

    def expand_one_indexblock(player, block):
        app_ids = []
        for i in range(0, len(block.data), 8):
            app_ids.append(btoi(block.data[i : i + 8]))
        return [DataBlock(algod=algod, app_id=app_id) for app_id in app_ids]

    def __init__(self, player, app_id=None, blocks=None):
        if blocks:
            index_blocks = IndexBlock.index_datablocks(player, blocks)
            layer = 1
            while len(index_blocks) > 1:
                print(f"baking {len(index_blocks)} into index layer {layer}")
                layer += 1
                txids = [block.burn(player) for block in index_blocks]
                index_appids = [
                    wait_for_confirmation(player.algod, txid)["application-index"]
                    for txid in txids
                ]
                index_blocks = IndexBlock.index_datablocks(
                    player,
                    [
                        DataBlock(algod=player.algod, app_id=index_appid, sync=True)
                        for index_appid in index_appids
                    ],
                )
            self.app_id = wait_for_confirmation(
                player.algod, index_blocks[0].burn(player)
            )["application-index"]
            self.data_blocks = blocks
        elif app_id:
            self.app_id = app_id
            self.data_blocks = IndexBlock.expand_indexblock(
                DataBlock(algod=player.algod, app_id=app_id)
            )

    def expand_indexblock(block):
        if block.block_type == DataBlock.BLOCK_TYPE_INDEX:
            index_blocks = IndexBlock.expand_one_indexblock(player, block)
            data_blocks = []
            for block in index_blocks:
                data_blocks += IndexBlock.expand_indexblock(block)
            return data_blocks
        if block.block_type == DataBlock.BLOCK_TYPE_DATA:
            return [block]


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
    block.py delete <file>
    block.py format
"""
    )
    if args["read"]:

        algod = algod.AlgodClient(os.environ["ALGOD_TOKEN"], os.environ["ALGOD_URL"])
        for block in IndexBlock(player, app_id=int(args["<app-id>"])).data_blocks:
            sys.stdout.buffer.write(block.data)

    if args["delete"]:
        app_ids_string = open(args["<file>"], "r").read().strip()
        app_ids = app_ids_string.split("\n")
        print(app_ids)
        DataBlock.delete_applications(player, [int(app_id) for app_id in app_ids])
    if args["format"]:
        DataBlock.delete_everything(player)

    elif args["write"]:
        data = open(args["<file>"], "rb").read()
        algod = algod.AlgodClient(os.environ["ALGOD_TOKEN"], os.environ["ALGOD_URL"])
        burn_result = DataBlock.big_burn(player, data)
        print(
            IndexBlock(
                player,
                blocks=[
                    DataBlock(player.algod, app_id=f)
                    for f in flatten([account[1:] for account in burn_result])
                ],
            ).app_id
        )
