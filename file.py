from algosdk.future import transaction
from disas import program_scratch
from pyteal import *
from algosdk.future import transaction
from algosdk import encoding
from util import (
    wait_for_confirmation,
    application_state,
    big_endian,
    Player,
    itob16,
    btoi16,
    itob32,
    btoi32,
)
from algosdk.v2client import algod
import base64
from docopt import docopt
from block2 import DataBlock


class FileRecordException(Exception):
    def __init__(self):
        pass


class FileRecord(DataBlock):
    FILE_RECORD_TYPE_LITERAL = 0x00
    FILE_RECORD_TYPE_REFERENCE = 0x01
    FILE_RECORD_MAX_SIZE = 100000

    def __init__(self, name, data=None, app_id=None):
        if not data and not app_id:
            raise Exception("Please specify app_id or data")
        pass

    def to_bytes(self):
        # FILE_RECORD_TYPE_LITERAL:
        # <0x00> <NAME_LEN(2)> <NAME> <DATA_LEN(4)> <DATA>
        # FILE_RECORD_TYPE_REFERENCE:
        # <0x01> <NAME_LEN(2)> <NAME> <REFERENCE(8)>
        return (
            bytes([0])
            + itob16(len(self.name))
            + self.name
            + itob16(len(self.data))
            + self.data
        )

    def from_bytes(byte_chunk_iter, load_references=False):
        buf = bytearray()
        byte_index = 0
        for byte_chunk in byte_chunk_iter:
            buf += byte_chunk
            while True:
                offset = 0
                try:
                    if buf[0] == FileRecord.FILE_RECORD_TYPE_LITERAL:
                        name_offset = btoi16(buf[1:3]) + 3
                        name = str(buf[3:name_offset])
                        offset = (
                            btoi32(buf[name_offset : name_offset + 4]) + name_offset
                        )
                        data = str(buf[name_offset:offset])
                        yield FileRecord(name, data)  # name, data, bytes_read
                    elif buf[0] == FileRecord.FILE_RECORD_TYPE_REFERENCE:
                        name_offset = btoi16(buf[1:3]) + 3
                        name = str(buf[3:name_offset])
                        offset = buf[name_offset : name_offset + 4] + name_offset
                        app_id = btoi(buf[name_offset:offset])
                        yield FileRecord(name, app_id=app_id)
                    else:
                        raise FileRecordException(
                            f"Invalid Data at byte index {byte_index}"
                        )
                    byte_index += offset
                    buf = buf[offset:]
                except IndexError:
                    if len(buf) > FileRecord.FILE_RECORD_MAX_SIZE:
                        raise FileRecordException(
                            f"Can't find end of file record, gave up at byte {byte_index}"
                        )
                    # load more data
                    break
