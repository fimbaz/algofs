#!/bin/bash
# Hopefully L2 will get too complex to manage in a bash script.  Until then...
if [[ $1 = nowait ]]; then
    NOWAIT=yep
    shift;
fi

if [[ $1 = dryrun ]]; then
    DRYRUN=yep
    shift;
fi
COMMAND=$1
# append str
if [[ $COMMAND = append ]]; then
    APP_ID_1=$2
    sudo -u algorand -E  goal app call \
	 --app-id $APP_ID_1 \
	 --app-arg "str:$COMMAND" \
	 --app-arg "str:$3" \
	 --from $HOT_WALLET_KEY \
	 $(if [[ $DRYRUN ]]; then echo --dryrun-dump  --out=/tmp/foo.dump; fi;) \
	 $(if [[ $NOWAIT ]]; then echo --no-wait; fi;) \
	&& if [[ $DRYRUN ]]; then sudo -E -u algorand goal clerk dryrun-remote   -D /tmp/foo.dump  --verbose; fi;
fi;
# copy from to
if [[ $COMMAND = copy ]]; then
    APP_ID_1=$2
    APP_ID_2=$3
    sudo -u algorand -E  goal app call \
	 --app-id $APP_ID_2 \
	 --foreign-app $APP_ID_1 \
	 --app-arg "str:$COMMAND" \
	 --app-arg "int:$4" \
	 --from $HOT_WALLET_KEY \
	 $(if [[ $NOWAIT ]]; then echo --no-wait; fi;) \
	 $(if [[ $DRYRUN ]]; then echo --dryrun-dump  --out=/tmp/foo.dump; fi;) \
	&& if [[ $DRYRUN ]]; then sudo -E -u algorand goal clerk dryrun-remote   -D /tmp/foo.dump  --verbose; fi;
fi;
if [[ $COMMAND = new ]]; then
    sudo -u algorand -E goal app create \
	 --creator $HOT_WALLET_KEY \
	 --global-byteslices 58 \
	 --global-ints 6 \
	 --local-byteslices 0 \
	 --local-ints 0 \
	 --approval-prog ${2:-algofs.teal} \
	 --clear-prog clear.teal | tail -n1 | cut -d ' ' -f6
fi
if [[ $COMMAND = settail ]]; then
    APP_ID_1=$2
    APP_ID_2=$3
    sudo -u algorand -E  goal app call \
	 --app-id $APP_ID_1 \
	 --foreign-app $APP_ID_2 \
	 --app-arg "str:$COMMAND" \
	 --from $HOT_WALLET_KEY \
	 $(if [[ $NOWAIT ]]; then echo --no-wait; fi;) \
	 $(if [[ $DRYRUN ]]; then echo --dryrun-dump  --out=/tmp/foo.dump; fi;) \
	&& if [[ $DRYRUN ]]; then sudo -E -u algorand goal clerk dryrun-remote   -D /tmp/foo.dump  --verbose; fi;
fi

if [[ $COMMAND = sethead ]]; then
    APP_ID_2=$2
    APP_ID_1=$3
    # Since there's no room in 2, copy the remaining data from 1 into 3
    sudo -u algorand -E  goal app call \
	 --app-id $APP_ID_2 \
	 --foreign-app $APP_ID_1 \
	 --app-arg "str:$COMMAND" \
	 --from $HOT_WALLET_KEY \
	 $(if [[ $NOWAIT ]]; then echo --no-wait; fi;) \
	 $(if [[ $DRYRUN ]]; then echo --dryrun-dump  --out=/tmp/foo.dump; fi;) \
	&& if [[ $DRYRUN ]]; then sudo -E -u algorand goal clerk dryrun-remote   -D /tmp/foo.dump  --verbose; fi;
fi

if [[ $COMMAND = read ]]; then
    sudo -u algorand -E goal app read --global --app-id $2 
fi
