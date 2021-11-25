#!/bin/bash
goal app create --creator $HOT_WALLET_KEY --global-byteslices 63 --global-ints 1 --local-byteslices 0 --local-ints 0 --approval-prog $1 --clear-prog clear.teal

