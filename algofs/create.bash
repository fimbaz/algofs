#!/bin/bash
sudo -u algorand -E goal app create --creator $HOT_WALLET_KEY --global-byteslices 61 --global-ints 3 --local-byteslices 0 --local-ints 0 --approval-prog $1 --clear-prog clear.teal

