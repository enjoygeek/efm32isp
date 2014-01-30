#!/usr/bin/env python2

from xmodem import XMODEM
import sys,os
import time
import serial


RESP_ERR = "unexpected response!"
def ERR(msg,ecode=0):
    sys.stderr.write(msg + os.linesep)
    if( ecode!= 0):
        exit(ecode)

def INFO(msg):
    sys.stdout.write(msg + os.linesep)

def CHK(bval, msg, ecode=0):
    if not bval:
        ERR(msg,ecode)


def get_response(ser):
    answer = ""
    resp=ser.read()
    while resp != "":
        answer += resp
        resp = ser.read()
    return answer

def handle_init(resp):
    lines = resp.split("\r\n")
    CHK( lines[0]=='', RESP_ERR,3)
    CHK( lines[1]=='', RESP_ERR,3)
    CHK( len(lines[2])==29, RESP_ERR,3)

    version,ignore,chipid = lines[2].split(" ")
    # line 3 is glitch due to UART-baud reconfiguration of bootloader
    CHK( lines[4]=='?', RESP_ERR,4)

    INFO( "Bootloader version: '%s' ChipID: '%s'" % (version,chipid) )
    return (version,chipid)


def upload(ser,path):
    f = open(path,"rb")

    ser.write('u')

    def ser_write(msg,timeout=1):
        ser.setWriteTimeout(timeout)
        return ser.write(msg)

    def ser_read(size,timeout=1):
        ser.setTimeout(timeout)
        return ser.read(size)

    modem = XMODEM(ser_read, ser_write)
    modem.send(f)

    ser.setTimeout(0)
    ser.setWriteTimeout(0)


def main(args):
    PORT = "/dev/ttyUSB0"
    BAUD = 57600
    MAIN = "bin/main.bin"
    ser = serial.Serial(PORT, BAUD, timeout=0, parity=serial.PARITY_NONE)
    ser.open()
    if not ser.isOpen():
        sys.stderr.write("Couldn't open serial port '" + PORT + "'!\n")
        sys.exit(1)

    sys.stdout.write("Put the chip into bootloader mode!\n")
    sys.stdout.write("Waiting for bootloader to respond ")
    sys.stdout.flush()
    resp = ""
    tries = 10
    while resp == "":
        #trigger auto baud rate configuration
        ser.write("U")
        time.sleep(1.0/10)
        resp = get_response(ser)
        for i in range(5):
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1.0/10)
        tries -= 1
        if tries < 0:
            INFO(" ERROR")
            ERR("Bootloader not responding!",2)
    INFO("") #newline

    handle_init(resp)
    upload(ser,MAIN)


    
if __name__ == "__main__":
    main(sys.argv)


#"1.60 ChipID: 20353500503EBB68"