#!/bin/bash
sudo -u algorand -E  goal app call --app-id $1 --app-arg "str:append" --app-arg "str:hello mr greenspan" --from UV65HPXNKRXPEUXSMQMZ766LT4NKAUK74SX2IAGCT6QB2TULDAQ5VJPGQU --dryrun-dump  --out=/tmp/foo.dump
echo dumpd
sudo -E -u algorand goal clerk dryrun-remote   -D /tmp/foo.dump  --verbose
