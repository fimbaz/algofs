#!/bin/bash
if [[ $1 = dryrun ]]; then
    DRYRUN=yep
    shift;
fi
COMMAND=$1
APP_ID_1=$2
if [[ $COMMAND = append ]]; then
    sudo -u algorand -E  goal app call \
	 --app-id $APP_ID_1 \
	 --app-arg "str:$COMMAND" \
	 --app-arg "str:$3" \
	 --from $HOT_WALLET_KEY \
	 $(if [[ $DRYRUN ]]; then echo --dryrun-dump  --out=/tmp/foo.dump; fi;) \
	&& if [[ $DRYRUN ]]; then sudo -E -u algorand goal clerk dryrun-remote   -D /tmp/foo.dump  --verbose; fi;
fi;
