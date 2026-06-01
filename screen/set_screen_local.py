import sys
import math


def _delete_all_buckets(self, upper):
    #self._switch_bucket(0, 2)
    for bI in range(upper):
        self._delete_bucket(bI)


def _clear_bucket(self, active_index):
    """Delete all buckets except active_index, twice each."""
    for i in range(16):
        if i != active_index:
            self._delete_bucket(i)
            self._delete_bucket(i)


def set_screen_local(self, channel, mode, value, **kwargs):
    """Set the screen mode and content.

    Unstable.

    Supported channels, modes and values:

    | Channel | Mode | Value |
    | --- | --- | --- |
    | `lcd` | `liquid` | — |
    | `lcd` | `brightness` | int between `0` and `100` (%) |
    | `lcd` | `orientation` | `0`, `90`, `180` or `270` (°) |
    | `lcd` | `static` | path to image |
    | `lcd` | `gif` | path to animated GIF |
    """

    assert channel.lower() == "lcd", "Invalid Channel, valid: lcd, provided: " + channel
    assert mode != None, "No mode specified"

    if mode != "liquid":
        assert value != None, f"Mode: {mode} needs a value"

    # get orientation and brightness
    self._write([0x30, 0x01])

    def parse_lcd_info(msg):
        self.brightness = msg[0x18]
        self.orientation = msg[0x1A]

    def _is_2023_fw_version2():
        device_product_id = self.device.product_id
        if device_product_id == 0x300E:
            self._get_fw_version()
            return self._fw[0] == 2
        return False

    self._read_until({b"\x31\x01": parse_lcd_info})

    if mode == "brightness":
        value_int = int(value)
        assert value_int >= 0 and value_int <= 100, "Invalid brightness value"
        self._write([0x30, 0x02, 0x01, value_int, 0x0, 0x0, 0x1, self.orientation])
        return
    elif mode == "orientation":
        value_int = int(value)
        assert (
            value_int == 0 or value_int == 90 or value_int == 180 or value_int == 270
        ), "Invalid orientation value"
        self._write([0x30, 0x02, 0x01, self.brightness, 0x0, 0x0, 0x1, int(value_int / 90)])
        return
    elif mode == "static":
        if _is_2023_fw_version2():
            data = self._prepare_static_file_rgb16(value, self.orientation)
            self._send_2023_data_fw2(
                data, [0x06, 0x0, 0x0, 0x0] + list(len(data).to_bytes(4, "little"))
            )
            self._send_2023_data_fw2(
                data, [0x06, 0x0, 0x0, 0x0] + list(len(data).to_bytes(4, "little"))
            )
            return

        # Inline _send_data to insert _clear_bucket after _switch_bucket
        data = self._prepare_static_file(value, self.orientation)
        bulk_info = [0x02, 0x0, 0x0, 0x0] + list(len(data).to_bytes(4, "little"))

        assert self.bulk_device, "Cannot find bulk out device"

        self._write_then_read([0x36, 0x03])

        buckets = self._query_buckets()
        bucket_index = self._find_next_unoccupied_bucket(buckets)
        bucket_index = self._prepare_bucket(
            bucket_index if bucket_index != -1 else 0, bucket_index == -1
        )

        header = [
            0x12, 0xFA, 0x01, 0xE8,
            0xAB, 0xCD, 0xEF, 0x98,
            0x76, 0x54, 0x32, 0x10,
        ] + bulk_info
        data_size = math.ceil((len(header) + len(data)) / 1024)
        data_size_bytes = list(data_size.to_bytes(2, "little"))

        memory_start = self._get_bucket_memory_offset(buckets, bucket_index, data_size)
        mid_index = -1
        if memory_start == -1:
            if bucket_index == 1:
                for bI in range(1, 16):
                    self._delete_bucket(bI)
                memory_start = [0x41, 0x06]
            else:
                mid_index = 0 if bucket_index == 0 else bucket_index - 1
                _delete_all_buckets(self, mid_index)
                bucket_index = 0
                memory_start = [0x0, 0x0]

        self._setup_bucket(bucket_index, bucket_index + 1, memory_start, data_size_bytes)
        self._write_then_read([0x36, 0x01, bucket_index])
        self._bulk_write(header)
        for i in range(0, len(data), self.bulk_buffer_size):
            self._bulk_write(list(data[i : i + self.bulk_buffer_size]))
        self._write([0x36, 0x02])

        self._switch_bucket(bucket_index)

        if mid_index != -1:
            for bI in range(max(mid_index, 1), 16):
                self._delete_bucket(bI)

        return

    elif mode == "gif":
        if _is_2023_fw_version2():
            raise NotImplementedError(
                "gif images are not supported on firmware 2.X.Y, please see issue #631"
            )
        data = self._prepare_gif_file(value, self.orientation)
        self._send_data(data, [0x01, 0x0, 0x0, 0x0] + list(len(data).to_bytes(4, "little")))
        return
    elif mode == "liquid":
        self._switch_bucket(0, 2)
        return

    # release device when finished
    if self.bulk_device and (mode == "static" or mode == "gif"):
        if sys.platform == "win32":
            self.bulk_device.close_winusb_device()
        else:
            self.bulk_device.release()

    raise TypeError("Invalid mode")
