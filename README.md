# MTreader

## What's this?

MTreader is a simple and small (under 200 SLOC) Python-based utility that aims to serve a single goal: read chunks of flash memory from MediaTek MT6261-based feature phones. It can also read firmware version before creating the readback, and supports displaying some decimal error codes from the platform itself if anything goes wrong. No other features are supported or even planned here.

MTreader runs on Python 3.2 and above and only requires pySerial module as a dependency.

## How to use it?

### Basic usage

```
python3 mtmaster.py port file start length
```

Example - backup all 4MB of flash memory (positions 0 to 4194304 on the device flash) into `rom.bin` file on Mac: `python3 mtreader.py /dev/tty.usbmodem14100 rom.bin 0 4194304` 

### Advanced usage

In case your phone requires a different DA (Download Agent) binary, you can also specify its parameters:

- `-a` - path to DA file
- `-s1` - DA stage 1 loading parameters in the `offset:size:addr` format with each value in hex (defaults to `0:0x718:0x70007000`)
- `-s2` - DA stage 2 loading parameters in the `offset:size:addr` format with each value in hex (defaults to `0x718:0x1e5c8:0x10020000`)

You can also adjust the readback block size as well with the `-bs` parameter. Changing it is not recommended if the default of 1024 bytes works for you.


## FAQ

### Which hardware is currently supported?

MT6261-based OEM phones that can open BROM port that can be seen as USB-Serial. Nokias (genuine ones) will generally not work. The rule of thumb is: if it can be handled by FlashTool v5.1420, then it can be handled by MTreader as well.

As for different MT6261 versions support, the tool had been successfully tested on various MT6261D and MT6261M handsets (provided they can also be supported by FlashTool). MT6261D still remains the primary target though.

### Why was this created then? Isn't FlashTool good enough?

No, it isn't. FlashTool is proprietary and single-platform. Having no viable open source alternative that can be run on any normal OS was enough to kickstart the research to create this tool.

Moreover, to in order to just create a flash dump with FlashTool, you'll need to:

1. Obtain some scatter file (even though it's totally unnecessary for the readback functionality) and load it into FlashTool.
2. Go to the "Readback" tab.
3. Remove all blocks there and create the block with the memory range you want in a tiny GUI window.
4. Select the path to save in another GUI window.
5. Press "Readback" and connect the device with perfect timing for it to be seen by the tool.
6. Probably reinsert the battery (if it's possible at all) after an unsuccessful or even successful operation.

With MTreader, you just need to:

1. Enter the command with four necessary parameters - port, output file, range start and range length.
2. Just disconnect the cable after a successful or unsuccessful operation - the tool will automatically send the hardware reset command anyway.

MTreader was created to only do one thing and try doing it well, and in no way is going to compete with any proprietary flashing or dumping solutions.

### How to detect the port file name?

Turn the phone off, insert the cable while holding the bootkey and see what device appears in `/dev` filesystem. On Linux, it most likely would be something like `/dev/ttyUSB0`. On Mac, it would look like `/dev/tty.usbmodem14100`.

### What is a bootkey?

It's a key that you hold to open the BROM serial port. It depends on the vendor. On most phones, it's Call key. On some phones, it can be arrow down key, # or something else.

### Where was information collected from?

There were three main sources of information: [mtk-open-tools](https://github.com/mtek-hack-hack/mtk-open-tools), [platform-quectel](https://github.com/Wiz-IO/platform-quectel/blob/master/builder/frameworks/MT6261.py) and - most importantly - my own research of FlashTool (running on a VM) USB traffic dumps necessary to combine the above sources, streamline them and make them work on real phone targets, not developer boards. Making the phone load the DA correctly was one thing but complete absence of understanding what to do next and figuring out the protocol to talk to DA itself was another challenge altogether.

### Will there be other chipset support?

Most probably, no. MT6261 is the simplest to implement because it uses 2-stage DA, while most other MediaTeks use 4 stages. However, the implementation is as straightforward and hackable as possible, so it shouldn't be a problem to add two other stages and thus other chipset support if absolutely necessary.

### Are there any plans to support flashing in addition to readbacks?

No. Not in this utility. Flashing MediaTek SoCs via USB is much more complicated than dumping. The process depends on the kind of partitions we're trying to flash, is generally quite fragile, relies on some proprietary, internal and undocumented logic, and in total requires much more research and rigorous testing on different devices with potential risk of bricking them to an unflashable state. When such research is complete, another utility will be published.
