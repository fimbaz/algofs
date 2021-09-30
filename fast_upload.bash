#!/bin/bash
while read FILE; do
    echo "$FILE" $(python block2.py write "$FILE" --txids  | bash txids2appids.bash | python block2.py write-index /dev/stdin)
done

