#!/bin/bash -e

python3 afkbot.py\
    --afk-channel $AFK_CHANNEL\
    --server $SERVER\
    --port $PORT\
    --nick $NICK\
    --certificate $CERTIFICATE\
    --idle-time $IDLE_TIME\
    --password $PASSWORD\
    --allow-self-signed
