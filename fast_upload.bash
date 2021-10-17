#!/bin/bash
while read FILE; do
    echo "$FILE" $(python algofs/block2.py write "$FILE" --txids  | bash txids2appids.bash | python algofs/block2.py write-index /dev/stdin)
done

