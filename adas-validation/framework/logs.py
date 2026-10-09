"""BLF/DBC decoding and a deliberately narrow DLT V1 verbose-string profile.

Real ECU DLT deployments require their own profile, endian, timestamp and
non-verbose/FIBEX support. Unsupported packets fail closed here.
"""
import struct
from pathlib import Path
import can
import cantools

DBC = Path(__file__).resolve().parents[1] / "data/adas.dbc"

def write_blf(path, samples):
    db = cantools.database.load_file(DBC)
    with can.BLFWriter(str(path)) as writer:
        for t, name, signals in samples:
            msg = db.get_message_by_name(name)
            writer.on_message_received(can.Message(timestamp=1700000000+t,
                arbitration_id=msg.frame_id, is_extended_id=False,
                data=msg.encode(signals), channel=0))

def read_blf(path):
    db = cantools.database.load_file(DBC)
    rows = []
    with can.BLFReader(str(path)) as reader:
        for frame in reader:
            if frame.is_error_frame or frame.is_remote_frame:
                raise ValueError("CAN error/remote frame in evidence")
            msg = db.get_message_by_frame_id(frame.arbitration_id)
            rows.append((frame.timestamp, msg.name, msg.decode(frame.data)))
    if not rows:
        raise ValueError("empty BLF")
    origin = rows[0][0]
    return [(round(t-origin, 6), name, values) for t, name, values in rows]

def write_dlt(path, events):
    # Storage header LE; standard header MSBF, WEID, WTMS, UEH, version 1.
    with Path(path).open("wb") as stream:
        for counter, (t, text) in enumerate(events):
            raw = text.encode("utf-8") + b"\0"
            payload = struct.pack(">IH", 0x00000200, len(raw)) + raw
            extended = struct.pack(">BB4s4s", 0x41, 1, b"ADAS", b"AEB1")
            optional = b"ECU1" + struct.pack(">I", round(t*10000))
            packet = struct.pack(">BBH", 0x37, counter % 256,
                4+len(optional)+len(extended)+len(payload)) + optional+extended+payload
            stream.write(struct.pack("<4sII4s", b"DLT\x01", 1700000000+int(t),
                round((t % 1)*1e6), b"ECU1") + packet)

def read_dlt(path):
    blob = Path(path).read_bytes()
    rows, pos = [], 0
    while pos < len(blob):
        if pos+20 > len(blob) or blob[pos:pos+4] != b"DLT\x01":
            raise ValueError("invalid/truncated DLT storage header")
        htyp, _, length = struct.unpack_from(">BBH", blob, pos+16)
        if htyp != 0x37 or length < 28 or pos+16+length > len(blob):
            raise ValueError("unsupported/truncated DLT profile")
        tick = struct.unpack_from(">I", blob, pos+24)[0]
        msin, argc, app, context = struct.unpack_from(">BB4s4s", blob, pos+28)
        typeinfo, size = struct.unpack_from(">IH", blob, pos+38)
        if (msin, argc, app, context, typeinfo) != (0x41,1,b"ADAS",b"AEB1",0x200):
            raise ValueError("unsupported DLT argument/profile")
        if 28+size != length or size < 1 or blob[pos+16+length-1] != 0:
            raise ValueError("invalid DLT string")
        rows.append((tick/10000, blob[pos+44:pos+44+size-1].decode("utf-8")))
        pos += 16+length
    if not rows:
        raise ValueError("empty DLT")
    return rows
