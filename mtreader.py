#!/usr/bin/env python3

import os, sys, struct, time
from serial import Serial

class MTreader:

    def __init__(self, devfile):
        while True:
            try:
                self.s = Serial(devfile, 115200)
                sys.stdout.write("\n")
                break
            except OSError as e:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(0.1)

    def send(self, data, sz = 0):
        r = ''
        if len(data):
            self.s.write(data)
        if sz > 0:
            r = self.s.read(sz)
        return r

    def cmd(self, cmd, sz = 0):
        r = ''
        cmdlen = len(cmd)
        if cmdlen > 0:
            assert(self.send(cmd, cmdlen) == cmd)
        if sz > 0:
            r = self.s.read(sz)
        return r

    def read16(self, addr, sz=1, endianness='>'):
        r = self.cmd(b'\xA2' + struct.pack('>II', addr, sz), sz*2)
        return struct.unpack(endianness + sz * 'H', r)

    def write16(self, addr, val):
        r = self.cmd(b'\xD2' + struct.pack(">II", addr, 1), 2)
        assert(r == b"\0\1")
        r = self.cmd(struct.pack(">H", val), 2)
        assert(r == b"\0\1")

    def read32(self, addr, sz=1, endianness=">"):
        r = self.cmd(b'\xD1' + struct.pack(">II", addr, sz), (sz*4)+4)
        return struct.unpack(endianness + "H" + (sz*'I')+"H", r)

    def write32(self, addr, val):
        r = self.cmd(b'\xD4' + struct.pack(">II", addr, 1), 2)
        assert(r == b"\0\1")
        r = self.cmd(struct.pack(">I", val), 2)
        assert(r == b"\0\1")

    def connect(self, timeout = 9.0):
        self.s.timeout = 0.1
        while True:
            self.s.write(b'\xA0')
            r = self.s.read(1)
            if r == b'\x5F':
                break
        self.s.write(b'\x0A\x50\x05')
        r = self.s.read(3)
        assert(r == b'\xF5\xAF\xFA')
        self.chip = self.read16(0x80000008)[0]
        self.write16(0xa0030000, 0x2200) # disable system watchdog
        self.write16(0xa0710074, 0x0001) # enable transfers from core to RTC
        self.write16(0xa0700a28, 0x8000) # enable USB download mode
        self.write16(0xa0700a24, 2) # disable battery watchdog
        self.write32(0xa0510000, 3) # enter memory map mode 3
        # now all flash is mapped as little-endian 32-bit chunks at 0x10000000

    def read_flash(self, outfile, start, size, blk_size=1024):
        outf = open(outfile, "wb")
        offset = 0
        addr = 0x10000000 + start
        while size > 0:
            rsize = min(size, blk_size)
            chunk = self.read32(addr, rsize>>2, '<')
            outchunk = struct.pack('>' + (len(chunk) - 2)*'L', *chunk[1:-1])
            size -= rsize
            addr += rsize
            outf.write(outchunk)
            sys.stdout.write(".")
            sys.stdout.flush()
        outf.close()

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
    parser.add_argument('-bs','--block-size', type=int, default=1024, help='Readback block size (in bytes), defaults to 1024')
    args = parser.parse_args()
    if(args.length < 1):
        print('Zero length of data, exiting')
        exit(1)
    print("Turn the phone off, hold the boot key and connect the cable")
    m = MTreader(args.port)
    print("Sending BROM handshake...")
    m.connect()
    print("Connected, chip ID: %04x" % m.chip)
    print("Dumping, don't disconnect...")
    m.read_flash(args.file, args.start, args.length, args.block_size)
    print("\nROM dumped, disconnect the cable")
    m.da_reset()
