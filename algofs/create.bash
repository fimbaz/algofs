#!/bin/bash
sudo -u algorand -E goal app create --creator $HOT_WALLET_KEY --global-byteslices 60 --global-ints 4 --local-byteslices 0 --local-ints 0 --approval-prog $1 --clear-prog clear.teal

