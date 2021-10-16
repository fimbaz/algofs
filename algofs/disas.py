from pyteal import *
from algosdk import account, encoding
from algosdk import util
import json
import base64


def dryrun(self, drr, **kwargs):
    data = json.dumps(drr).encode()
    req = "/teal/dryrun"
    headers = {"Content-Type": "application/msgpack"}
    kwargs["headers"] = headers
    return self.algod_request("POST", req, data=data, **kwargs)


def program_scratch(algod, approval_program, clear_program, app_id=None,hot_wallet=None):
    hot_wallet = hot_wallet
    data = dryrun(
        algod,
        drr={
            "accounts": [
                {
                    "address": hot_wallet if hot_wallet else "VCZCQGZ3BOKZQPE6J3QWRJPPEV4RFH2QK4SN7WP377RX447B3PKU4GM6XQ",
                    "amount": 1000000000,
                    "amount-without-pending-rewards": 1000000000,
                    "created-apps": [
                        {
                            "id": app_id if app_id else 1000000001,
                            "params": {
                                "approval-program": approval_program,
                                "clear-state-program": clear_program,
                                "creator": hot_wallet,
                                "global-state-schema": {
                                    "num-byte-slice": 7,
                                    "num-uint": 7,
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
                    "id": app_id,
                    "params": {
                        "approval-program": approval_program,
                        "clear-state-program": clear_program,
                        "creator": hot_wallet,
                        "global-state-schema": {"num-byte-slice": 7, "num-uint": 7},
                    },
                }
            ],
            "latest-timestamp": 1,
            "round": 1,
            "sources": None,
            "txns": [
                {
                    "txn": {
                        "apaa": ["aW5mbw=="],
                        "apid": app_id,
                        "fee": 1000,
                        "fv": 1,
                        "type": "appl",
                    }
                }
            ],
        },
    )
    info_array = [
        (val["uint"] or val["bytes"]) for val in data["txns"][0]["app-call-trace"][-1]["scratch"]
    ]
    return info_array


if __name__ == "__main__":
    hot_account = "VQS455TFEPLPSBOT6JEQZ5R46ZG6P4PWNHOHKQ72TARJDCJ42CEOO3KVPU"
    owner = Player(
        hot_account=hot_account,
        algod_url="http://127.0.0.1:4003",
        kmd_url="http://127.0.0.1:4004",
        indexer_url="http://127.0.0.1:8092",
    )
    program_scratch(
        owner,
        454,
        "AiAOAAUEAgEK6AdkMqCNBhcfA8CEPSYUBHJlbnQDYmV0BGZsaXAFY2xhaW0EcmFrZQtzZXQtY2FzaGllcgZ1bnJlbnQHcGx1bmRlcgRpbmZvC3JlbnRlZFVudGlsBlBsYXllcgNDdXQERmxpcAVTdGFrZQhEZXBvc2l0cwdDYXNoaWVyBlJlbnRlcgdUb3BkZWNrCXJlbnRhbEZlZQdDcmVhdG9yMRgiEkAD1DEZIxJAA8YxGSQSQAO4MRklEkADqjEZIQQSQAOfNhoAKBJAAwM2GgApEkACnTYaACoSQAI7NhoAKxJAAWU2GgAnBBJAAQs2GgAnBRJAANg2GgAnBhJAAHw2GgAnBxJAACQ2GgAnCBJAAAEAIQU1JiEGNSchBzUoIQY1KSEINSohCTUrIkMnCWQhCAkyBg0iJwplNSA1ITQgECInC2U1IjUjNCIQIicMZTUkNSU0JBQQMwAHJwpkEhAzAAgnDWQlCyEJCBIQQAACIkMnDiJnIQRDQgMIMRYhBBIyBCUSEDMAECEEEhAnD2QzAAASECcQZDMABxIQIicKZTUENQU0BBQQQAACIkMnCWknEGknEWknDWknC2knDGknCmknEmknDmkhBENCArUxACcTZBIiJwllNQA1ATQAMgYnCWQMEBQQQAACIkMnDzYaAWchBENCAosiJxNlNQI1AzQCJxNkMwAHEhAiJwllNQA1ATQAMgYnCWQMEBQQJw5kIhIRQAACIkMnCWknEGknEWknDWknC2knDGknCmknEmknDmkhBENCAjoyBCUSMwAQIQQSEDMAACcPZBIQMwAJMgMSECInDGU1GDUZNBgQIicKZTUaNRs0GhAiJwtlNRw1HTQcECInDWU1HjUfNB4QJwxkIQohC1IXJwtkIQohC1IXGyEEGjUWIQQzAAcnEGQSCDUXNBZAAAsnCjUUJxA1FUIACCcQNRQnCjUVIQQQMwAHNBRkEjMACCcNZCULIQkIEhAnDmQ0FxoQMwAHNBVkEjMACCEJEhAnDmQ0FxoQERBAAAIiQycONBchDBsnDmQaZyEEQ0IBbDEbJRIyBCEEEhAiJwplNQw1DTQMECInEWU1DjUPNA4QIicLZTUQNRE0EBAiJwxlNRI1EzQSFBA2GgEDJxFkEhBAAAIiQycMNhoBZycJJwlkIQUIZyEEQ0IBEjEbJRIzAAAzAQASEDMABycPZBIQMwAIJw1kIQkIEhAiJwplNQg1CTQIFBAiJxFlNQo1CzQKEEAAAiJDJws2GgFnJwozAABnJw4nDmQlGWcnCScJZCEFCGchBENCALQxFiEEEjIEJRIQMwAQIQQSEDEbIQwSEDMABycPZBIQIicQZTUGNQc0BhQQNhoCFzMACAwQMwAIIQkJNhoCFwkhCQ0QNhoCFyEJDRA2GgIXIQ0MEEAAAiJDJxE2GgFnJxAxAGcnDicOZCEEGWcnCTIGNhoCFyEGCghnJxI2GgIXZycNMwAINhoCFwkhCQlnIQRDQgAgIQRDMQAnE2QSQzEAJxNkEkMxACcTZBJDJxMxAGchBEM=",
        "AiABASJD",
    )

