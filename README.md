# MTreader

## What's this?

MTreader is a simple and small (under 100 SLOC) Python-based utility that aims to serve a single goal: read chunks of flash memory from MediaTek MT626x-based feature phones. No other features are supported or even planned here.

MTreader runs on Python 3.2 and above and only requires pySerial module as a dependency.

## How to use it?

```
python3 mtreader.py port file start length
```

Example - backup all 4MB of flash memory (positions 0 to 4194304 on the device flash) into `rom.bin` file on Mac:

```
python3 mtreader.py /dev/tty.usbmodem14100 rom.bin 0 4194304
``` 

You can also adjust the readback block size as well with the `-bs` parameter. Changing it is not recommended if the default of 1024 bytes works for you.


## FAQ

### Which hardware is currently supported?

MT6261-based OEM phones that can open BROM port that can be seen as USB-Serial. Nokias (genuine ones) will generally not work, unless connected without a battery.

As for different MT6261 versions support, the tool had been successfully tested on various MT6261D and MT6261M handsets (provided they can also be supported by FlashTool). MT6261D still remains the primary target though.

Also, at least one MT6260A-based phone had also been successfully dumped with this tool - Nokia 5310 DS (TA-1212). To run the dumping, connect the 5310 without a battery and then insert it. Disconnect the cable and the battery after the process.

### Why was this created then? Isn't FlashTool good enough?

No, it isn't. First of all, FlashTool is proprietary and single-platform. Having no viable open source alternative that can be run on any normal OS was enough to kickstart the research to create this tool.

Second, MTreader works on a lower level than FlashTool, so it can handle some phones in bricked state that FlashTool refuses to see or requires some non-standard DA to operate on them. Some of the many examples include Philips E106 or a bricked Maxcom MM817 with corrupted bootloader area where DA becomes unresponsive after sending it.

Moreover, to in order to just create a flash dump with FlashTool, you'll need to:

1. Obtain some scatter file (even though it's totally unnecessary for the readback functionality) and load it into FlashTool.
2. Probably also obtain the necessary Download Agent file if the one shipped with FlashTool doesn't work with your model.
3. Go to the "Readback" tab.
4. Remove all blocks there and create the block with the memory range you want in a tiny GUI window.
5. Select the path to save in another GUI window.
6. If working without battery, check another checkbox in the option menu.
7. Press "Readback" and connect the device holding the bootkey with perfect timing for it to be seen by the tool.
8. If working with battery, probably reinsert it (if it's possible at all) after an unsuccessful or even successful operation.

With MTreader, you just need to:

1. Enter the command with four necessary parameters - port, output file, range start and range length.
2. Connect the cable holding the bootkey when asked, regardless of whether or not the phone has a battery in it.
3. Just disconnect the cable after a successful or unsuccessful operation - the tool will automatically send the hardware reset command anyway.

MTreader was created to only do one thing and try doing it well, and in no way is going to compete with any proprietary flashing or dumping solutions.

### How to detect the port file name?

Turn the phone off, insert the cable while holding the bootkey and see what device appears in `/dev` filesystem. On Linux, it most likely would be something like `/dev/ttyUSB0`. On Mac, it would look like `/dev/tty.usbmodem14100`.

### What is a bootkey?

It's a key that you hold to open the BROM serial port. It depends on the vendor. On most phones, it's Call key. On some phones, it can be arrow down key, # or something else.

### How is the tool working without a DA binary?

Yes, MTreader used a DA in the past, but now it's completely blob-free (and this allowed to move it to the [public domain](./UNLICENSE)) and works via BROM itself. The trick is in using the correct mapping register setting: when we set the 32-bit value at the `0xa0510000` to 2, all the ROM contents (in 32-bit little-endian chunks) are mapped onto zero base address by the MT626x chipset itself.

### Where was information collected from?

There were several main sources of information: [mtk-open-tools](https://github.com/mtek-hack-hack/mtk-open-tools), [platform-quectel](https://github.com/Wiz-IO/platform-quectel/blob/master/builder/frameworks/MT6261.py), [Fernly](https://github.com/xobs/fernly) and - most importantly - my own research of FlashTool (running on a VM) USB traffic dumps necessary to combine the above sources, streamline them and make them work on real phone targets, not developer boards.

### Will there be other chipset support?

Most probably, no, but you may try.

### Are there any plans to support flashing in addition to readbacks?

No. Not in this utility. Flashing MediaTek SoCs via USB is much more complicated than dumping. The process is generally quite fragile, relies on more proprietary, internal and undocumented logic, and in total requires much more research and rigorous testing on different devices with potential risk of bricking them to an unflashable state. When such research is complete, another utility will be published.

### Are there any plans to move to direct USB access instead of relying on the USB-Serial drivers installed in the OS?

Yes, there are some plans to create a PyUSB-based version and then a browser-based JS port (using WebUSB). This would unlock the access to the devices with non-standard BROM ports not seen by the USB-Serial drivers for some reason (including but not limited to most MTK-based Nokia S30+ phones).

However, for this to happen, first all known issues (stated in the section below) need to be solved. Second, as this would drastically increase the codebase size, it might be wiser to do this porting as a part of a larger effort, for instance, when creating the universal utility for dumping and flashing after the research on the latter is complete.

## Known issues

- Reset-after-dump functionality doesn't have stable behavior (so it's not recommended to dump phones with non-removable batteries for now)
