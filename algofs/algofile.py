from algosdk.future import transaction
import pathlib
import os
from disas import program_scratch
from pyteal import *
from algosdk.future import transaction
from algosdk import encoding
from util import (
    wait_for_confirmation,
    application_state,
    big_endian,
    Player,
    btoi,
    itob16,
    btoi16,
    itob32,
    btoi32,
)
from algosdk.v2client import algod
import base64
from docopt import docopt
from block2 import DataBlock


class FileRecord:
    FILE_RECORD_TYPE_LITERAL = 0x00
    FILE_RECORD_TYPE_REFERENCE = 0x01
    FILE_RECORD_MAX_SIZE = 100000000

    def __init__(self, name, data=None, app_id=None):
        if app_id:
            pass  # TODO
        elif data and name:
            self.data = data
            self.name = name
        else:
            raise Exception("Please specify app_id or data + name")

    def write_to_fs(self, root):
        # TODO: make this streaming
        destination_path = os.path.join(root, self.name)
        dirname = os.path.dirname(destination_path)
        if not os.path.isdir(dirname):
            pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
        handle = open(destination_path, "wb")
        handle.write(self.data)
        handle.close()

    def to_bytes(self):
        # TODO: make this streaming
        # FILE_RECORD_TYPE_LITERAL:
        # <0x00> <FLAGS(2)> <NAME_LEN(2)> <NAME> <DATA_LEN(4)> <DATA>
        # FILE_RECORD_TYPE_REFERENCE:
        # <0x01> <FLAGS(2)> <NAME_LEN(2)> <NAME> [SHA256SUM(32)] <REFERENCE(8)>
        # <RESERVED(1)> [bits0-6 reserved] <SHASUM[7]>
        bin_name = self.name.encode("utf-8")
        return (
            bytes([0, 0, 0])
            + itob16(len(bin_name))
            + bin_name
            + itob32(len(self.data))
            + self.data
        )

    def from_bytes(byte_chunk_iter, load_references=False):
        buf = bytearray()
        byte_index, next_record_start = 0, 0
        for byte_chunk in byte_chunk_iter:
            buf += byte_chunk
            while buf:
                try:
                    if buf[0] == FileRecord.FILE_RECORD_TYPE_LITERAL:
                        flags = buf[1:3]
                        if flags[1] & 0x03:
                            pass
                            # Trusted directory
                        name_end = btoi16(buf[3:5]) + 5
                        name = buf[5:name_end]
                        data_length = btoi32(buf[name_end : name_end + 4])
                        data_start = name_end + 4
                        data_end = data_start + data_length
                        buf[data_end - 1] # force exception
                        data = buf[data_start:data_end]
                        next_record_start = data_end
                        yield FileRecord(
                            name.decode("utf-8"), data
                        )  # name, data, bytes_read
                    elif buf[0] == FileRecord.FILE_RECORD_TYPE_REFERENCE:
                        name_offset = btoi16(buf[3:5]) + 5
                        name = str(buf[3:name_offset])
                        next_record_start = (
                            buf[name_offset : name_offset + 4] + name_offset
                        )
                        app_id = btoi(buf[name_offset:next_record_start])
                        yield FileRecord(
                            name=name.decode("utf-8"),
                            app_id=app_id,
                            load_references=load_references,
                        )
                    else:
                        raise Exception(f"Invalid Data at byte index {byte_index}")
                    byte_index += next_record_start
                    buf = buf[next_record_start:]
                    next_record_start = 0
                except IndexError:
                    if len(buf) > FileRecord.FILE_RECORD_MAX_SIZE:
                        raise Exception(
                            "Can't find end of file record, gave up at byte {byte_index}"
                        )
                    # load more data
                    break


if __name__ == "__main__":
    records = [
        *FileRecord.from_bytes(
            [
                b"".join(
                    [
                        FileRecord(
                            name="file.txt",
                            data=b"Hello mother, hello father, hello world at, Glasgow",
                        ).to_bytes(),
                        FileRecord(
                            name="buff_fun_with_greb_and_bilby.txt",
                            data=b"This is where I would put my blog!",
                        ).to_bytes(),
                    ]
                )
            ]
        )
    ]
    for record in records:
        print(record.name)
        print(record.data)
