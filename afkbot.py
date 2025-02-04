#!/usr/bin/env python

#Copyright (c) 2013-2022 Charles Ricketts <chuck.the.pc.guy@gmail.com>
#
#    Copyright (c) 2022, Charles Ricketts <chuck.the.pc.guy@gmail.com>
#    All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of AFKBot nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
#    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#    DISCLAIMED. IN NO EVENT SHALL AFKBOT'S CONTRIBUTORS BE LIABLE FOR ANY
#    DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#Contains code from mumblebee
#Copyright (c) 2013, Toshiaki Hatano <haeena@haeena.net>
#
#Contains code from the eve-bot
#Copyright (c) 2009, Philip Cass <frymaster@127001.org>
#Copyright (c) 2009, Alan Ainsworth <fruitbat@127001.org>
#
#Contains code from the Mumble Project:
#Copyright (C) 2005-2009, Thorvald Natvig <thorvald@natvig.com>
#
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions
#are met:
#
#- Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#- Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#- Neither the name of localhost, 127001.org, eve-bot nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE FOUNDATION OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import socket
import time
import struct
import sys
import select
import _thread
import threading
import signal
import os
import optparse
import platform
import random
#import daemon
import configparser

import pdb
from pprint import pprint
#The next 2 imports may not succeed
warning=""
try:
    import ssl
    from ssl import SSLContext
except:
    print("ERROR: This python program requires the python ssl module (available in python 2.6; standalone version may be at found http://pypi.python.org/pypi/ssl/)\n")
    print(warning)
    sys.exit(1)

import importlib.util
if importlib.util.find_spec('google') == None or importlib.util.find_spec("google.protobuf") == None:
    print("ERROR: Google protobuf library not found. This can be installed via 'pip install protobuf'")
    sys.exit(1)

try:
    import Mumble_pb2
except:
    print("Error: Module Mumble_pb2 not found\nIf the file 'Mubmle_pb2.py' does not exist, then you must compile it with 'protoc --python_out=. Mumble.proto' from the script directory.")
    sys.exit(1)

headerFormat=">HI"
eavesdropper=None
controlbreak = False
messageLookupMessage={Mumble_pb2.Version:0,Mumble_pb2.UDPTunnel:1,Mumble_pb2.Authenticate:2,Mumble_pb2.Ping:3,Mumble_pb2.Reject:4,Mumble_pb2.ServerSync:5,
        Mumble_pb2.ChannelRemove:6,Mumble_pb2.ChannelState:7,Mumble_pb2.UserRemove:8,Mumble_pb2.UserState:9,Mumble_pb2.BanList:10,Mumble_pb2.TextMessage:11,Mumble_pb2.PermissionDenied:12,
        Mumble_pb2.ACL:13,Mumble_pb2.QueryUsers:14,Mumble_pb2.CryptSetup:15,Mumble_pb2.ContextActionModify:16,Mumble_pb2.ContextAction:17,Mumble_pb2.UserList:18,Mumble_pb2.VoiceTarget:19,
        Mumble_pb2.PermissionQuery:20,Mumble_pb2.CodecVersion:21,Mumble_pb2.UserStats:22,Mumble_pb2.RequestBlob:23,Mumble_pb2.ServerConfig:24,Mumble_pb2.SuggestConfig:25}
messageLookupNumber={}
threadNumber=0

for i in messageLookupMessage.keys():
        messageLookupNumber[messageLookupMessage[i]]=i

class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger("mumblebot.log")
sys.stderr = sys.stdout

def discontinue_processing(signl, frme):
    global eavesdropper
    print("%s: Received shutdown notice." % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"),));
    if signl == signal.SIGUSR1:
        pbMess = Mumble_pb2.TextMessage()
        pbMess.actor = eavesdropper.session
        for channel_id in eavesdropper.channelList:
            pbMess.channel_id.append(channel_id)
        pbMess.message = "Server rebooting!"
        eavesdropper.sendTotally(eavesdropper.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString()))
    if eavesdropper:
        eavesdropper.wrapUpThread()
    else:
        sys.exit(0)
    global controlbreak;
    controlbreak = True;

signal.signal( signal.SIGINT, discontinue_processing )
#signal.signal( signal.SIGQUIT, discontinue_processing )
signal.signal( signal.SIGTERM, discontinue_processing )
signal.signal( signal.SIGUSR1, discontinue_processing )

class timedWatcher(threading.Thread):
    def __init__(self,socketLock,socket):
        global threadNumber
        threading.Thread.__init__(self)
        self.pingTotal=1
        self.isRunning=True
        self.socketLock=socketLock
        self.socket=socket
        i = threadNumber
        threadNumber+=1
        self.threadName="Thread " + str(i)

    def stopRunning(self):
        self.isRunning=False

    def run(self):
        self.nextPing=time.time()-1

        while self.isRunning:
            t=time.time()
            if t>self.nextPing:
                pbMess = Mumble_pb2.Ping()
                pbMess.timestamp=(self.pingTotal*5000000)
                pbMess.good=0
                pbMess.late=0
                pbMess.lost=0
                pbMess.resync=0
                pbMess.udp_packets=0
                pbMess.tcp_packets=self.pingTotal
                pbMess.udp_ping_avg=0
                pbMess.udp_ping_var=0.0
                pbMess.tcp_ping_avg=50
                pbMess.tcp_ping_var=50
                self.pingTotal+=1
                packet=struct.pack(headerFormat,3,pbMess.ByteSize())+pbMess.SerializeToString()
                self.socketLock.acquire()
                while len(packet)>0:
                    sent=self.socket.send(packet)
                    packet = packet[sent:]
                self.socketLock.release()
                self.nextPing=t+10
            #sleeptime=self.nextPing-t
            #if sleeptime > 0:
            time.sleep(0.5)
        print("%s: timed thread going away" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"),));

class mumbleConnection(threading.Thread):
    def __init__(self,host=None,nickname=None,channel=None,delay=None,limit=None,password=None,verbose=False,certificate=None,idletime=30,allow_self_signed=0):
        global threadNumber
        i = threadNumber
        threadNumber+=1
        self.threadName="Thread " + str(i)
        threading.Thread.__init__(self)
        tcpSock=socket.socket(type=socket.SOCK_STREAM)
        self.socketLock=_thread.allocate_lock()
        #self.ssl_context=ssl.SSLContext()
        #self.ssl_context.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)
        #self.ssl_context.load_cert_chain(certificate)
        self.socket=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.socket.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)
        self.socket.load_cert_chain(certificate)
        if allow_self_signed:
            if not os.path.exists("server.pem"):
                print("Downloading server certificate")
                cert=ssl.get_server_certificate(host, ssl.PROTOCOL_TLS_CLIENT)
                with open("server.pem","wb") as file:
                    file.write(cert.encode('utf-8'))
            self.socket.load_verify_locations(cafile="server.pem")
            self.socket.check_hostname=False
        self.socket=self.socket.wrap_socket(tcpSock,server_hostname=host[0])
        #self.socket=ssl.wrap_socket(tcpSock,certfile=certificate,ssl_version=ssl.PROTOCOL_TLS_CLIENT)
        self.socket.setsockopt(socket.SOL_TCP,socket.TCP_NODELAY,1)
        self.host=host
        self.nickname=nickname
        self.inChannel=False
        self.session=None
        self.channelId=None
        self.userList={}
        self.userListByName={}
        self.channelList={}
        self.channelListByName={}
        self.readyToClose=False
        self.timedWatcher = None
        # TODO: Implement delay and rate limit
        #self.delay=delay
        #self.limit=limit
        self.password=password
        self.verbose=verbose
        self.server_certificate=None

        #######################################
        # AFKBot-specific config
        #######################################
        self.idleLimit=idletime #Idle limit in minutes
        self.channel=channel #AFK channel to listen in
    def decodePDSInt(self,m,si=0):
        v = ord(m[si])
        if ((v & 0x80) == 0x00):
            return ((v & 0x7F),1)
        elif ((v & 0xC0) == 0x80):
            return ((v & 0x4F) << 8 | ord(m[si+1]),2)
        elif ((v & 0xF0) == 0xF0):
            if ((v & 0xFC) == 0xF0):
                return (ord(m[si+1]) << 24 | ord(m[si+2]) << 16 | ord(m[si+3]) << 8 | ord(m[si+4]),5)
            elif ((v & 0xFC) == 0xF4):
                return (ord(m[si+1]) << 56 | ord(m[si+2]) << 48 | ord(m[si+3]) << 40 | ord(m[si+4]) << 32 | ord(m[si+5]) << 24 | ord(m[si+6]) << 16 | ord(m[si+7]) << 8 | ord(m[si+8]),9)
            elif ((v & 0xFC) == 0xF8):
                result,length=decodePDSInt(m,si+1)
                return(-result,length+1)
            elif ((v & 0xFC) == 0xFC):
                return (-(v & 0x03),1)
            else:
                print("%s: Help help, out of cheese :(" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"),))
                sys.exit(1)
        elif ((v & 0xF0) == 0xE0):
            return ((v & 0x0F) << 24 | ord(m[si+1]) << 16 | ord(m[si+2]) << 8 | ord(m[si+3]),4)
        elif ((v & 0xE0) == 0xC0):
            return ((v & 0x1F) << 16 | ord(m[si+1]) << 8 | ord(m[si+2]),3)
        else:
            print("%s: out of cheese?" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"),))
            sys.exit(1)

    def packageMessageForSending(self,msgType,stringMessage):
        length=len(stringMessage)
        return struct.pack(headerFormat,msgType,length)+stringMessage

    def sendTotally(self,message):
        self.socketLock.acquire()
        while len(message)>0:
            sent=self.socket.send(message)
            if sent < 0:
                print("[%s] %s: Server socket error while trying to write, immediate abort" % (self.threadName,time.strftime("%a, %d %b %Y %H:%M:%S +0000"),))
                self.socketLock.release()
                return False
            message=message[sent:]
        self.socketLock.release()
        return True

    def readTotally(self,size):
        message=bytes()
        while len(message)<size:
            received=self.socket.recv(size-len(message))
            message+=received
            if len(received)==0:
                print("%s: Server socket died while trying to read, immediate abort" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"),))
                return None
        return message

    def parseMessage(self,msgType,stringMessage):
        msgClass=messageLookupNumber[msgType]
        message=msgClass()
        message.ParseFromString(stringMessage)
        return message

    def joinChannel(self):
        if self.channelId!=None and self.session!=None:
            pbMess = Mumble_pb2.UserState()
            pbMess.session=self.session
            pbMess.channel_id=self.channelId
            if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                self.wrapUpThread()
                return
            self.inChannel=True

    def wrapUpThread(self):
        #called after thread is confirmed to be needing to die because of kick / socket close
        self.readyToClose=True

    def readPacket(self):
        #pdb.set_trace()
        meta=self.readTotally(6)
        if not meta:
            self.wrapUpThread()
            return
        msgType,length=struct.unpack(headerFormat,meta)
        stringMessage=self.readTotally(length)
        if not stringMessage:
            self.wrapUpThread()
            return
        #Type 1 = UDP Tunnel, voice data
        if msgType==1:
            session,sessLen=self.decodePDSInt(stringMessage,1)
            if session in self.userList and self.userList[session]["channel"] == self.channelListByName[self.channel]:
                if "idlesecs" in self.userList[session] and "oldchannel" in self.userList[session]["idlesecs"]:
                    pbMess = Mumble_pb2.UserState()
                    pbMess.session = session
                    pbMess.actor = self.session
                    pbMess.channel_id = self.userList[session]["idlesecs"]["oldchannel"]
                    if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                         self.wrapUpThread()
        #Type 5 = ServerSync
        if (not self.session) and msgType==5 and (not self.inChannel):
            message=self.parseMessage(msgType,stringMessage)
            self.session=message.session
            self.joinChannel()
        #Type 6 = ChannelRemove
        if msgType == 6:
            message=self.parseMessage(msgType,stringMessage)
            channelid=message.channel_id
            for item in self.channelListByName:
                if self.channelListByName[item] == message.channel_id:
                    del self.channelListByName[item]
                    break
            for item in self.userList:
                if "idlesecs" in self.userList[item] and "oldchannel" in self.userList[item]["idlesecs"]:
                    if self.userList[item]["idlesecs"]["oldchannel"] == channelid:
                        self.userList[item]["idlesecs"]["oldchannel"] = 0;
        #Type 7 = ChannelState
        if msgType == 7: #(not self.inChannel) and msgType==7 and self.channelId==None:
            message=self.parseMessage(msgType,stringMessage)
            if message.channel_id not in self.channelList or self.channelList[message.channel_id] != message.name:
                self.channelList[message.channel_id]=message.name
                self.channelListByName[message.name]=message.channel_id
            if (not self.inChannel) and self.channelId==None:
                if self.channel==None and message.channel_id==0:
                    self.channel=message.name
                    self.channelId=message.channel_id
                    self.joinChannel()
                if message.name==self.channel:
                    self.channelId=message.channel_id
                    self.joinChannel()
        #Type 8 = UserRemove (kick)
        if msgType==8:
            message=self.parseMessage(msgType,stringMessage)
            if self.session!=None:
                if message.session==self.session:
                    print("[%s] %s: ********** KICKED **********" % (self.threadName,time.strftime("%a, %d %b %Y %H:%M:%S +0000"),))
                    self.wrapUpThread()
                    return
            session=message.session
            if session in self.userList:
                temp = self.userList[session]
                del self.userListByName[self.userList[session]["name"]]
                del self.userList[session]
        #Type 9 = UserState
        if msgType==9:
            message=self.parseMessage(msgType,stringMessage)
            session=message.session
            if session in self.userList:
                record=self.userList[session]
            else:
                record={"session":session}
                self.userList[session]=record
            name=None
            channel=None
            if message.HasField("name"):
                name=message.name
                if "name" in record and record["name"] in self.userListByName:
                    del self.userListByName[record["name"]]
                record["name"]=name
                self.userListByName[name]=message.session
            if message.HasField("channel_id"):
                channel=message.channel_id
                record["channel"]=channel
            if name and not channel:
                record["channel"]=0
            channelName = self.channelList[record["channel"]]
            #If they're not already in the AFK channel
            if message.channel_id != self.channelListByName[self.channel]:
                #Send a query for UserStats -- needed to get idletime
                if "idlesecs" in record:
                    record["idlesecs"]["checksent"] = True
                    record["idlesecs"]["oldchannel"] = message.channel_id
                else:
                    record["idlesecs"]={"checksent":True,"oldchannel":message.channel_id}
                if message.HasField("actor"): # and message.actor != self.session:
                    record["idlesecs"]["checksent"] = False
                    record["idlesecs"]["checkon"] = time.time()+self.idleLimit*60
                else:
                    pbMess = Mumble_pb2.UserStats()
                    pbMess.session = session
                    if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                        self.wrapUpThread()
            else:
                if "idlesecs" in record:
                    record["idlesecs"]["checksent"] = False
                    record["idlesecs"]["checkon"] = -1
#                    if "oldchannel" not in record["idlesecs"]:
##                        record["idlesecs"]["oldchannel"] = 0
#                    else:
#                        record["idlesecs"]["oldchannel"] = message.channel_id
                else:
                    record["idlesecs"]={"checksent":False,"checkon":-1,"oldchannel":0}
            if self.inChannel and channelName == "Private Chats":
                pbMess = Mumble_pb2.TextMessage();
                pbMess.actor = self.session;
                pbMess.session.append(message.session);
                pbMess.message = "This is the Private Chats channel. To create a sub-channel, right click Private Chats and select 'Add'. Name your channel and check the 'Temporary' checkbox.";
                if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                    self.wrapUpThread()
            if self.inChannel and channelName in ("Castle Wars","Zamorak","Saradomin"):
                #Package a message to the user
                pbMess = Mumble_pb2.TextMessage();
                pbMess.actor = self.session;
                pbMess.session.append(message.session);
                pbMess.message = "Welcome to the Castle Wars channels! In this channel setup you can set up a hotkey for Shout with a target of the parent channel to send messages to the opposing team.";
                if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                    self.wrapUpThread()
            return

        #Type 11 = TextMessage
        if msgType==11:
            message=self.parseMessage(msgType,stringMessage)
            if message.actor!=self.session:
                if message.message.startswith("/roll"):
                    pbMess = Mumble_pb2.TextMessage()
                    pbMess.actor = self.session
                    pbMess.channel_id.append(self.channelId)
                    pbMess.channel_id.append(self.userList[message.actor]["channel"])
                    pbMess.message = self.userList[message.actor]["name"] + " rolled " + str(random.randint(0,100))
                    pbMess.session.append(self.session)
                    if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                        self.wrapUpThread()
                    return
                if message.message.startswith("/afkme"):
                    pbMess = Mumble_pb2.UserState()
                    pbMess.session = message.actor
                    pbMess.actor = self.session
                    pbMess.channel_id = self.channelListByName[self.channel]
                    if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                        self.wrapUpThread()
                    self.userList[message.actor]["idlesecs"]["checkon"] = -1
                    return
                if message.message.startswith("/afk"):
                    args = message.message.split(" ",1)
                    if len(args) == 1:
                      return
                    pbMess = Mumble_pb2.UserState()
                    for key in self.userListByName:
                        if key.lower() == args[1].lower():
                            pbMess.session = self.userListByName[key]
                    print(pbMess.session);
                    if pbMess.session == 0:
                        pbMess = Mumble_pb2.TextMessage();
                        pbMess.actor = self.session;
                        pbMess.session.append(message.actor);
                        pbMess.message = "No such user to AFK";
                        if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                            self.wrapUpThread()
                        return
                    pbMess.actor = self.session
                    pbMess.channel_id = self.channelListByName[self.channel]
                    if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                        self.wrapUpThread()
                    self.userList[pbMess.session]["idlesecs"]["checkon"] = -1
                    return
                if message.message.startswith("/unafk"):
                    args = message.message.split(" ",1)
                    if len(args) == 1:
                      return
                    pbMess = Mumble_pb2.UserState()
                    for key in self.userListByName:
                        if key.lower() == args[1].lower():
                            pbMess.session = self.userListByName[key]
                            pbMess.channel_id = self.userList[pbMess.session]["idlesecs"]["oldchannel"]
                    if pbMess.session == 0:
                        pbMess = Mumble_pb2.TextMessage();
                        pbMess.actor = self.session;
                        pbMess.session.append(message.actor);
                        pbMess.message = "No such user to UnAFK";
                        if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                            self.wrapUpThread()
                        return
                    pbMess.actor = self.session
                    if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                        self.wrapUpThread()
                    self.userList[pbMess.session]["idlesecs"]["checkon"] = -1

        #Type 12 = PermissionDenied
        if msgType==12:
            print("Permission Denied.")
            return

        #Type 22 = UserStats
        if msgType==22:
            message=self.parseMessage(msgType,stringMessage)
            self.userList[message.session]["idlesecs"]["idlesecs"] = message.idlesecs
            self.userList[message.session]["idlesecs"]["checkon"] = time.time()+((self.idleLimit*60)-message.idlesecs)
            if message.idlesecs > self.idleLimit*60 and message.session != self.session:
                #Move user to AFK channel
                pbMess = Mumble_pb2.UserState()
                pbMess.session = message.session
                pbMess.actor = self.session
                pbMess.channel_id = self.channelListByName[self.channel];
                if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                    self.wrapUpThread()
                self.userList[message.session]["idlesecs"]["checkon"] = -1
            self.userList[message.session]["idlesecs"]["checksent"] = False
            return


    def run(self):
        try:
            self.socket.connect(self.host)
        except Exception as inst:
            print(inst)
            print("%s: Couldn't connect to server" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"),))
            global controlbreak
            controlbreak=True
            return
        self.socket.setblocking(False)
        print("[%s] %s: Connected to server" % (self.threadName,time.strftime("%a, %d %b %Y %H:%M:%S +0000")))
        pbMess = Mumble_pb2.Version()
        pbMess.release="1.2.8"
        pbMess.version=66052
        pbMess.os=platform.system()
        pbMess.os_version="AFKBot0.5.0"

        initialConnect=self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())

        pbMess = Mumble_pb2.Authenticate()
        pbMess.username=self.nickname
        if self.password!=None:
            pbMess.password=self.password
        celtversion=pbMess.celt_versions.append(-2147483637)

        initialConnect+=self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())

        if not self.sendTotally(initialConnect):
            return

        sockFD=self.socket.fileno()

        self.timedWatcher = timedWatcher(self.socketLock,self.socket)
        self.timedWatcher.start()
        print("[%s] %s: started timed watcher %s" % (self.threadName,time.strftime("%a, %d %b %Y %H:%M:%S +0000"),self.timedWatcher.threadName))

        while True:
            pollList,foo,errList=select.select([sockFD],[],[sockFD],5)
            for item in pollList:
                if item==sockFD:
                    try:
                        self.readPacket()
                    except ssl.SSLError:
                        continue
            for session in self.userList:
                record = self.userList[session]
                if "idlesecs" in record:
                    if record["name"] != self.nickname and record["idlesecs"]["checksent"] == False and record["idlesecs"]["checkon"] > -1 and record["idlesecs"]["checkon"] < time.time():
                        pbMess = Mumble_pb2.UserStats();
                        pbMess.session = session
                        if not self.sendTotally(self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())):
                            self.wrapUpThread()
                        record["idlesecs"]["checksent"] = True
            if self.readyToClose:
                self.wrapUpThread()
                break

        if self.timedWatcher:
            self.timedWatcher.stopRunning()

        self.socket.close()
        print("[%s] %s: waiting for timed watcher to die..." % (self.threadName,time.strftime("%a, %d %b %Y %H:%M:%S +0000")));
        if self.timedWatcher!=None:
            while self.timedWatcher.is_alive():
                pass
        print("[%s] %s: thread going away - %s" % (self.threadName,time.strftime("%a, %d %b %Y %H:%M:%S +0000"),self.nickname))

def main():
    global eavesdropper,warning,controlbreak

    p = optparse.OptionParser(description='Mumble 1.2 AFKBot',
                prog='afkbot.py',
                version='%prog 0.5.0',
                usage='\t%prog')

    p.add_option("-a","--afk-channel",help="Channel to eavesdrop in (default %%Root)",action="store",type="string",default="AFK")
    p.add_option("-s","--server",help="Host to connect to (default %default)",action="store",type="string",default="localhost")
    p.add_option("-p","--port",help="Port to connect to (default %default)",action="store",type="int",default=64738)
    p.add_option("-n","--nick",help="Nickname for the AFKBot (default %default)",action="store",type="string",default="AFKBot")
    p.add_option("-c","--certificate",help="Certificate file for the bot to use when connecting to the server (.pem)",action="store",type="string",default="afkbot.pem")
    p.add_option("-i","--idle-time",help="Time (in minutes) before user is moved to the AFK channel",action="store",type="int",default=30);
    p.add_option("-v","--verbose",help="Outputs and translates all messages received from the server",action="store_true",default=False)
    p.add_option("--password",help="Password for server, if any",action="store",type="string")
    p.add_option("-S","--allow-self-signed",help="Allow self-signed certificates",action="store_true",default=False)

    if len(warning)>0:
        print(warning)
    o, arguments = p.parse_args()
    if len(warning)>0:
        sys.exit(1)

    host=(o.server,o.port)

    #daemoninstance = daemon.DaemonContext()
    #daemoninstance.stdout = logfile;
    #daemoninstance.1

    while True:
        eavesdropper = mumbleConnection(host,o.nick,o.afk_channel,delay=None,limit=None,password=o.password,verbose=o.verbose,certificate=o.certificate,idletime=o.idle_time,allow_self_signed=o.allow_self_signed)
        eavesdropper.start()

        #Need to keep main thread alive to receive shutdown signal

        while eavesdropper.is_alive():
            time.sleep(0.5)

        if controlbreak == True:
            break

    return 0

if __name__ == '__main__':
        main()
