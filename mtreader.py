#!/usr/bin/env python3

import os, sys, struct, time
from serial import Serial

# status constants
NONE = b''
CONT = b'\x69'
ACK = b'\x5A'
NACK = b'\xA5'

class MTreader:

    def __init__(self, devfile, da_path, stage_1, stage_2, fio):
        self.da_path = da_path
        self.st1_offset, self.st1_size, self.st1_addr = [int(x, 16) for x in stage_1.split(":")]
        self.st2_offset, self.st2_size, self.st2_addr = [int(x, 16) for x in stage_2.split(":")]
        self.fio = int(fio, 16)
        while True:
            try:
                self.s = Serial(devfile, 115200)
                sys.stdout.write("\n")
                break
            except OSError as e:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(0.1)

    def crc_word(self, data, chs=0):
        for b in data:
            chs += b
        return chs & 0xFFFF

    def send(self, data, sz = 0):
        r = ""
        if len(data):
            self.s.write(data)
        if sz > 0:
            r = self.s.read(sz)
        return r

    def cmd(self, cmd, sz = 0):
        r = ""
        cmdlen = len(cmd)
        if cmdlen > 0:
            assert(self.send(cmd, cmdlen) == cmd)
        if sz > 0:
            r = self.s.read(sz)
        return r

    def da_read16(self, addr, sz=1):
        r = self.cmd(b'\xA2' + struct.pack(">II", addr, sz), sz*2)
        return struct.unpack(">" + sz * 'H', r)

    def da_write16(self, addr, val):
        r = self.cmd(b'\xD2' + struct.pack(">II", addr, 1), 2)
        assert(r == b"\0\1")
        r = self.cmd(struct.pack(">H", val), 2)
        assert(r == b"\0\1")

    def da_write32(self, addr, val):
        r = self.cmd(b'\xD4' + struct.pack(">II", addr, 1), 2)
        assert(r == b"\0\1")
        r = self.cmd(struct.pack(">I", val), 2)
        assert(r == b"\0\1")

    def da_send_da(self, address, size, data, block=4096):
        r = self.cmd(b'\xD7' + struct.pack(">III", address, size, block), 2)
        assert(r == b"\0\0")
        while data:
            self.s.write(data[:block])
            data = data[block:]
        r = self.cmd(NONE, 4) # checksum         

    def get_da(self, offset, size):
        self.fd.seek(offset)
        data = self.fd.read(size)
        return data

    def connect(self, timeout = 9.0):
        self.s.timeout = 0.02
        while True:
            self.s.write(b"\xA0")
            if self.s.read(1) == b"\x5F":
                self.s.write(b"\x0A\x50\x05")
                r = self.s.read(3)
                if r == b"\xF5\xAF\xFA":
                    break
                else:
                    print("BROM connection error")
                    exit(2)
            timeout -= self.s.timeout
            if timeout < 0:
                print("Timeout error")
                exit(2)
        self.s.timeout = 1.0
        self.CPU_HW = self.da_read16(0x80000000)[0]
        self.CPU_SW = self.da_read16(0x80000004)[0]
        self.chip = self.da_read16(0x80000008)[0]
        self.CPU_SB = self.da_read16(0x8000000C)[0]
        self.da_write16(0xa0700a28, 0x4010)
        self.da_write16(0xa0700a00, 0xF210)
        self.da_write16(0xa0030000, 0x2200)
        self.da_write16(0xa071004c, 0x1a57)
        self.da_write16(0xa071004c, 0x2b68)
        self.da_write16(0xa071004c, 0x042e)
        self.da_write16(0xa0710068, 0x586a)
        self.da_write16(0xa0710074, 0x0001)
        self.da_write16(0xa0710068, 0x9136)
        self.da_write16(0xa0710074, 0x0001)
        self.da_write16(0xa0710000, 0x430e)
        self.da_write16(0xa0710074, 0x0001)
        self.da_write32(0xa0510000, 0x00000002)

    def da_start(self):
        assert(os.path.isfile(self.da_path) == True)
        self.fd = open(self.da_path, "rb")
        # Send DA first stage
        offset = self.st1_offset
        size = self.st1_size
        data = self.get_da(offset, size)
        self.da_send_da(self.st1_addr, size, data, 0x400)
        # Send DA second stage
        offset = self.st2_offset
        size = self.st2_size
        data = self.get_da(offset, size)
        self.da_send_da(self.st2_addr, size, data, 0x800)
        # Pass execution to DA
        r = self.cmd(b'\xD5' + struct.pack(">I", self.st1_addr), 2)
        assert r == b"\0\0"
        r = self.cmd(NONE, 4)
        self.send(b"\xa5\x05\xfe\x00\x08\x00\x70\x07\xff\xff\x02\x00\x00\x01\x08", 1) # something undocumented
        #Set flash ID info and other stuff
        offset = self.fio
        for i in range(512):
            data = self.get_da(offset, 36)
            assert(data[:4] != b'\xFF\xFF\0\0')
            offset += 36
            r = self.send(data, 1)
            if r == ACK:
                assert(self.cmd(NONE, 2) == b'\xA5\x69')
                break
            assert(r == CONT)
        r = self.send(b"\0\0\0\0", 256)

    def get_version(self):
        self.send(b'\xEF', 1)
        r = self.send(b'\xEF', 256)
        r = r[:64].strip(b'\0')
        return r

    def da_read_flash(self, start, size, outfile, blk_size=1024):
        r = self.send(b'\xD6\0' + struct.pack(">LL", start, size), 1)
        if r == NACK:
            errorcode = self.s.read(4)
            print('Flash read error: %d, exiting' % int.from_bytes(errorcode, 'big'))
            self.da_reset()
            exit(1)
        self.send(struct.pack(">L", blk_size), 0)
        outf = open(outfile, "wb")
        while size > 0:
            chunk = self.s.read(min(size, blk_size))
            size -= len(chunk)
            chksum = struct.unpack(">H", self.s.read(2))[0]
            chksum_ref = self.crc_word(chunk)
            assert(chksum_ref == chksum)
            outf.write(chunk)
            sys.stdout.write(".")
            sys.stdout.flush()
            self.s.write(ACK) # continue with the next packet

    def da_reset(self):
        r = self.send(b'\xB9', 1)
        r = self.send(b'\xC9\x00', 1)
        r = self.send(b'\xDB\x01\x40\x00\x00\x00\x00', 1)

if __name__ == "__main__": # main app start
    from argparse import ArgumentParser
    parser = ArgumentParser(description="MTreader: a simple, no-nonsense MediaTek MT6261 phone ROM reader", epilog="(c) Luxferre 2020 --- No rights reserved")
    parser.add_argument('port', help='Serial port to connect to (/dev/ttyUSB0, /dev/tty.usbmodem14100 etc.)')
    parser.add_argument('file', help='File to write the dump into')
    parser.add_argument('start', type=int, help='start position (in the phone flash memory)')
    parser.add_argument('length', type=int, help='data length')
    parser.add_argument('-da','--agent', default=os.path.dirname(os.path.realpath(__file__))+'/default-da.bin', help='Path to download agent (DA) binary')
    parser.add_argument('-s1','--stage-1', default='0:0x718:0x70007000', help='Data for first stage DA loading (offset:size:addr format)')
    parser.add_argument('-s2','--stage-2', default='0x718:0x1e5c8:0x10020000', help='Data for second stage DA loading (offset:size:addr format)')
    parser.add_argument('-fio','--flash-info-offset', default='0x1ece0', help='Flash info offset in the DA file (hex)')
    parser.add_argument('-bs','--block-size', type=int, default=1024, help='Readback block size (in bytes), defaults to 1024')
    args = parser.parse_args()
    if(args.length < 1):
        print('Zero length of data, exiting')
        exit(1)
    print("Turn the phone off, hold the boot key and connect the cable")
    m = MTreader(args.port, args.agent, args.stage_1, args.stage_2, args.flash_info_offset)
    m.connect()
    if m.chip != 0x6261:
        print("Warning: chip ID is detected as %04x instead of 6261, readback process might fail!" % m.chip)
    m.da_start()
    print("DA sent and responsive, starting the operation")
    ver = m.get_version().decode('ascii')
    print("Firmware version: %s\n" % ver)
    print("Dumping, don't disconnect...")
    m.da_read_flash(args.start, args.length, args.file, args.block_size)
    print("\nROM dumped, disconnect the cable")
    m.da_reset()
