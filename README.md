# AFKBot #
Copyright (C) 2013-2015 Charles Ricketts  &lt;chuck.the.pc.guy@gmail.com&gt;

### Purpose ###
Unlike other voice chat clients, Mumble does not provide a mechanism to specify an AFK channel or timeout. So, I made a bot script that takes care of this for me. Though I am releasing this script in 2015, I have been using it without problems for a couple of years now. For my uses in a moderately trafficked Mumble server, it has been very stable.

### Features ###
* Configurable AFK timeout
* Channel the user was removed from is remembered
* While in the AFK channel, if a user talks they are removed from the AFK channel.

### Prerequisites ###
1. Python SSL, Python 2.6+ has this built in. Otherwise, it's available from http://pypi.python.org/pypi/ssl/
2. Mumble_pb2.py, prebuilt. If changes are made to the Mumble protocol in the future, a new Mumble_pb2.py may have to be generated. In order to build this file requires the Google Protobuffer tools located at http://code.google.com/apis/protocolbuffers/. Once installed, run `protoc python_out=[dir] Mumble.proto`. Mumble.proto is available from the Mumble source or Git repository.

### Arguments ###
    Usage: 	afkbot.py
    
    Mumble 1.2 AFKBot
    
    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -e EAVESDROP_IN, --eavesdrop-in=EAVESDROP_IN
                            Channel to eavesdrop in (default %%Root)
      -s SERVER, --server=SERVER
                            Host to connect to (default localhost)
      -p PORT, --port=PORT  Port to connect to (default 64738)
      -n NICK, --nick=NICK  Nickname for the eavesdropper (default AFKBot2)
      -d DELAY, --delay=DELAY
                            Time to delay response by in seconds (default 0)
      -l LIMIT, --limit=LIMIT
                            Maximum response per minutes (default 0, 0 =
                            unlimited)
      -c CERTIFICATE, --certificate=CERTIFICATE
                            Certificate file for the bot to use when connecting to
                            the server (.pem)
      -a AFK_CHANNEL, --afk-channel=AFK_CHANNEL
                            Designated AFK channel name
      -i IDLE_TIME, --idle-time=IDLE_TIME
                            Time (in minutes) before user is moved to the AFK
                            channel
      -v, --verbose         Outputs and translates all messages received from the
                            server
      --password=PASSWORD   Password for server, if any

### License ###

    Copyright (c) 2015, Charles Ricketts <chuck.the.pc.guy@gmail.com>
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of AFKBot nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL AFKBOT'S CONTRIBUTORS BE LIABLE FOR ANY
    DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
