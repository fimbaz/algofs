POSTGRES_DB=algorand
(i=0; while read; do echo $i $REPLY; i=$((i+1)); done; ) | tee "/tmp/$REPLY" | psql -c  "CREATE TEMPORARY TABLE app_txids(id SERIAL PRIMARY KEY,txid bytea NOT NULL);copy app_txids from stdin DELIMITERS ' ';copy (select app_txids.id,txn.asset from app_txids,txn where txn.txid = app_txids.txid) to stdout" $POSTGRES_DB | tr '\t' ' ' | cut -d' ' -f2
