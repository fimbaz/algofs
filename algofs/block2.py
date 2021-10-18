import gevent
from gevent import monkey

monkey.patch_all()
import itertools
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
    compress_ranges
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

monkey.patch_all()


class DataBlock(object):
    MAX_BLOCK_SIZE = 7000  # 1024 * 7  # might have to play with this.
    BLOCK_ACCOUNT_DEPOSIT = 9800000
    MAX_APPS_PER_ACCOUNT = 10
    BLOCK_TYPE_DATA = 1
    BLOCK_TYPE_INDEX = 2
    BLOCK_TYPE_FILE = 3
    BLOCK_TYPE_DIRECTORY = 4

    def __init__(
        self,
        algod=None,
        block_type=0,
        app_id=None,
        data=None,
        sync=False,
        load=True,
        account=None,
    ):
        if not (app_id or data) or (app_id and data):
            raise ValueError("specify either app_id or data")
        if data:
            program_data = DataBlock.compile_programs(
                algod,
                DataBlock.approval_program(data, block_type),
                DataBlock.clear_program(),
            )
        else:
            (program_data, data, block_type) = (
                DataBlock.load_programs(algod, app_id) if load else (None, None, None)
            )
        DataBlock.initialize(
            self, algod, app_id, program_data, data, block_type, account
        )

    def initialize(self, algod, app_id, program_data, data, block_type, account):
        self.algod = algod
        self.program_data = program_data
        self.data = data
        self.block_type = block_type
        self.app_id = app_id
        self.account = account

    def burn(self, player, account=None, sync=False, sign=True, send=True):
        while True:
            self.account = account if not self.account else self.account
            player.params.first = self.algod.ledger_supply()["current_round"]
            player.params.last = player.params.first + 100
            txn = transaction.ApplicationCreateTxn(
                player.hot_account if not self.account else self.account,
                player.params,
                approval_program=base64.b64decode(self.program_data[0]),
                clear_program=base64.b64decode(self.program_data[1]),
                on_complete=transaction.OnComplete.NoOpOC,
                global_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
                local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
                extra_pages=3,
            )
            if not sign:
                return txn
            signed_txn = player.wallet.sign_transaction(txn)
            if not send:
                return signed_txn
            try:
                self.txn_result = player.algod.send_transaction(signed_txn)
                break
            except algosdk.error.AlgodHTTPError as e:
                message = json.loads(str(e))["message"]
                print("retry", file=sys.stderr)
                print(message)
                if "TransactionPool.Remember: fee" in message or "txn dead" in message:
                    gevent.sleep(10)
                else:
                    raise e
        self.txid = self.txn_result
        if sync:
            self.app_id = wait_for_confirmation(player.algod, self.txn_result)[
                "application-index"
            ]
            return self.app_id
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


# 1. a block is read from the stream
# 2. an account is found for the block to live in
# 3. if necessary, an account funding txn is created and signed
# 4. an applicationcreate txn is created and signed
# input: 64 bit unsigned integer
# output: 8 byte big-endian representation of same

MAX_APPS_PER_ACCOUNT = 10
MAX_TXNS_PER_GROUP = 11
APP_DEPOSIT = 2000000
MAX_BLOCK_SIZE = 7000


def chunked_file(file_obj, chunk_size):
    while True:
        data = file_obj.read(chunk_size)
        if not data:
            break
        yield data


def chunked(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def data_to_blocks(player, data_iter, block_type=DataBlock.BLOCK_TYPE_DATA):
    for block in data_iter:
        yield DataBlock(player.algod, block_type=block_type, data=block)


def list_all_applications(player):
    for key in player.wallet.list_keys():
        info = player.algod.account_info(key)
        for app in info['created-apps']:
            yield app['id']
def list_keys_forever(player, start_with_current=False):
    if start_with_current:
        initial_keys = player.wallet.list_keys()
    else:
        initial_keys = []
    for key in initial_keys:
        yield key
    while True:
        yield player.wallet.generate_key()


class AccountAllocator:
    def __init__(self, player):
        self.player = player
        self.keys_iter = list_keys_forever(player)
        self.deficit = 0
        self.pending_deficit = 0
        self.app_slots_left = 0
        self.next_account = None
        self.pending_account = None

    def allocate_storage(self, block_iter):
        return self._batch_transactions(self._allocate_accounts(block_iter))

    def _allocate_accounts(self, block_iter):
        # NOT REENTRANT.  Add a lock up here before you try to use this in a threaded context
        while True:
            if self.app_slots_left == 0:
                self.next_account = next(self.keys_iter)
                self.account_info = self.player.algod.account_info(self.next_account)
                self.app_slots_left = MAX_APPS_PER_ACCOUNT - len(
                    self.account_info["created-apps"]
                )
            else:
                try:
                    while self.app_slots_left > 0:
                        self.app_slots_left -= 1
                        required_balance = APP_DEPOSIT * (10 - self.app_slots_left)
                        deficit = (
                            required_balance - self.account_info["amount"]
                            if required_balance > self.account_info["amount"]
                            else 0
                        )
                        yield (next(block_iter), self.next_account, deficit)
                except StopIteration:
                    break

    def _batch_transactions(self, blockaccountdeficit_iter):
        txns = deque([])
        # Not thread safe yet. TODO: add a lock.
        for block, account, deficit in blockaccountdeficit_iter:
            if not self.pending_account:
                self.pending_account = account
            elif account != self.pending_account:
                if self.pending_deficit != 0:
                    txns.appendleft(
                        transaction.PaymentTxn(
                            player.hot_account,
                            player.params,
                            self.pending_account,
                            self.pending_deficit,
                        ),
                    )
                self.pending_deficit = 0
                self.pending_account = account
                txns_to_yield = txns
                txns = deque([])
                yield txns_to_yield
            block.account = account
            self.pending_deficit += deficit
            txns.append(block)
        if self.pending_deficit and self.pending_account:
            txns.insert(
                0,
                transaction.PaymentTxn(
                    player.hot_account,
                    player.params,
                    self.pending_account,
                    self.pending_deficit,
                ),
            )
        self.pending_deficit = 0
        self.deficit = 0
        self.app_slots_left = 0  # use extra accounts to avoid conflicts
        txns_out = txns
        txns = deque([])
        yield txns_out


def _commit_txn(player, txn, blocks=False, sync=True):
    if isinstance(txn, DataBlock):
        app_id = txn.burn(player, sync=sync, send=True, sign=True)
        return (
            txn if blocks else app_id
        )  # result['application-index'] if 'application-index' in result else None
    else:
        while True:
            try:
                txn.first_valid_round = player.algod.ledger_supply()["current_round"]
                txn.last_valid_round = player.params.first + 100
                signed_txn = player.wallet.sign_transaction(txn)
                txid = player.algod.send_transaction(signed_txn)
                result = wait_for_confirmation(
                    player.algod, txid
                )  # wait for funding txns to happen
                break
            except algosdk.error.AlgodHTTPError as e:
                message = json.loads(str(e))["message"]
                print("retry", file=sys.stderr)
                print(message)
                if "TransactionPool.Remember: fee" in message or "txn dead" in message:
                    gevent.sleep(10)
                else:
                    raise e
        return


def commit_txns_for_accounts(player, txns_by_account_iter, blocks=False, txid=False):
    active_groups = deque([])
    application_txns = deque([])
    queue_level = 1
    for txns in itertools.chain(txns_by_account_iter, [[]]):
        if txns:
            commit_batch = _commit_txns_for_account(player, txns, blocks, txid=txid)
            active_groups.append([next(commit_batch), commit_batch])
        else:
            queue_level = 0
        while len(active_groups) > 8 * queue_level:
            active_group = active_groups.popleft()
            gevent.joinall([active_group[0]])[0].value
            application_txns.append(active_group[1])
        while len(application_txns) > 2 * queue_level:
            group = next(application_txns.popleft())
            finished_group = gevent.joinall(group)
            for job in group:
                if job.value is not None:
                    yield job.value


def _commit_txns_for_account(player, txns, blocks=False, txid=False):
    if not isinstance(txns[0], DataBlock):
        yield gevent.spawn(_commit_txn, player, txns.popleft(), blocks)
    else:
        yield gevent.spawn(len, "")

    yield (
        [
            gevent.spawn(_commit_txn, player, txn, blocks, sync=(not txid))
            for txn in txns
        ]
    )


def data_from_appids(algod, app_id_iter):
    for app_id in app_id_iter:
        yield DataBlock(algod, app_id=app_id).data


def index_datablocks(player, burned_block_iter):
    out = bytearray()
    for block in burned_block_iter:
        out += itob(block.app_id if isinstance(block, DataBlock) else block)
        if len(out) >= DataBlock.MAX_BLOCK_SIZE:
            yield DataBlock(
                player.algod, block_type=DataBlock.BLOCK_TYPE_INDEX, data=out
            )
            out = bytearray()
    if out:
        block = DataBlock(player.algod, block_type=DataBlock.BLOCK_TYPE_INDEX, data=out)
        yield block


def index_up_datablocks(player, allocator, data_block_iter):
    index_block_iter = commit_txns_for_accounts(
        player,
        allocator.allocate_storage(index_datablocks(player, data_block_iter)),
        blocks=True,
    )
    layer = [*index_block_iter]
    if len(layer) > 1:
        next_layer = index_up_datablocks(player, allocator, layer)
        if not next_layer:
            return layer
        layer = next_layer
    if len(layer) == 1:
        return layer


def expand_one_indexblock(player, block):
    app_ids = []
    for i in range(0, len(block.data), 8):
        app_ids.append(btoi(block.data[i : i + 8]))
    return [DataBlock(algod=player.algod, app_id=app_id) for app_id in app_ids]


def expand_one_indexblock_iter(player, block, indexes):
    contains_datablocks = False
    first_indexed_block = DataBlock(
        algod=player.algod, app_id=btoi(block.data[0:8]), load=True
    )
    if first_indexed_block.block_type == DataBlock.BLOCK_TYPE_DATA:
        contains_datablocks = True
    yield first_indexed_block
    for i in range(8, len(block.data), 8):
        indexed_block = DataBlock(
            algod=player.algod,
            app_id=btoi(block.data[i : i + 8]),
            load=(not (contains_datablocks and indexes)),
        )
        yield indexed_block


def expand_indexblock_iter(player, block, indexes=False):
    if block.block_type == DataBlock.BLOCK_TYPE_DATA or block.block_type == None:
        yield block
    if block.block_type == DataBlock.BLOCK_TYPE_INDEX:
        if indexes:
            yield block
        for some_block in expand_one_indexblock_iter(player, block, indexes):
            for data_block in expand_indexblock_iter(
                player, some_block, indexes=indexes
            ):
                yield data_block


def blocks_from_appids(player, appids_iter):
    for app_id in appids_iter:
        yield DataBlock(algod=player.algod, app_id=int(app_id), load=False)


def expand_indexblock(player, block):
    if block.block_type == DataBlock.BLOCK_TYPE_INDEX:

        index_blocks = expand_one_indexblock(player, block)
        data_blocks = deque([])
        for block in index_blocks:
            data_blocks += expand_indexblock(player, block)
    if block.block_type == DataBlock.BLOCK_TYPE_DATA:
        print(".", file=sys.stderr, flush=True, end="")
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
    block.py readappids <file>
    block.py write <file> [--txids]
    block.py write-index <file>
    block.py write-indexed <file>
    block.py show-pending
    block.py read-indexed [<app-id>] [--app-ids] [--ranges]
    block.py delete <file>
    block.py format
"""
    )
    if args["readappids"]:
        datafile = open(args["<file>"], "rb")
        for line in datafile.readlines():
            sys.stdout.buffer.write(DataBlock(player.algod, app_id=int(line)).data)

    if args["write-indexed"]:
        allocator = AccountAllocator(player)
        file_obj = open(args["<file>"], "rb")
        algod = algodclient.AlgodClient(
            os.environ["ALGOD_TOKEN"], os.environ["ALGOD_URL"]
        )
        print(
            index_up_datablocks(
                player,
                allocator,
                commit_txns_for_accounts(
                    player,
                    allocator.allocate_storage(
                        data_to_blocks(
                            player, chunked_file(file_obj, DataBlock.MAX_BLOCK_SIZE)
                        )
                    ),
                ),
            )[0].app_id
        )
    if args["read-indexed"]:
        app_ids = []
        if args["--app-ids"] and not args["<app-id>"]:
            for app_id in list_all_applications(player):
                print(app_id,flush=True)
            exit(0)
        for block in expand_indexblock_iter(
            player,
            DataBlock(player.algod, app_id=int(args["<app-id>"])),
            indexes=(args["--app-ids"] or args["--ranges"]),
        ):
            if args["--app-ids"]:
                print(str(block.app_id))
            elif args["--ranges"]:
                app_ids.append(block.app_id)
            else:
                sys.stdout.buffer.write(block.data)
        if args["--ranges"]:
            for block_range in [*compress_ranges(iter(sorted(app_ids)))]:
                print(f"{block_range[0]} {block_range[1]}")
    if args["show-pending"]:
        txns = player.algod.pending_transactions()
        print(txns)
    if args["write-index"]:
        file_obj = open(args["<file>"], "rb")
        allocator = AccountAllocator(player)
        print(
            index_up_datablocks(
                player, allocator, blocks_from_appids(player, file_obj.readlines())
            )[0].app_id
        )

    if args["format"]:
        print(list_all_applications(player))
                
    if args["write"]:
        allocator = AccountAllocator(player)
        file_obj = open(args["<file>"], "rb")
        file_size = os.path.getsize(args["<file>"])
        blocks_tot = file_size / DataBlock.MAX_BLOCK_SIZE
        algod = algodclient.AlgodClient(
            os.environ["ALGOD_TOKEN"], os.environ["ALGOD_URL"]
        )
        txids = []
        for txid in commit_txns_for_accounts(
            player,
            allocator.allocate_storage(
                data_to_blocks(player, chunked_file(file_obj, DataBlock.MAX_BLOCK_SIZE))
            ),
            txid=args["--txids"],
        ):
            print(txid, flush=True)
