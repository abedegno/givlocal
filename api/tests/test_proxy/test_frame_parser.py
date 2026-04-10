"""Tests for the GivEnergy frame parser."""

from givlocal.proxy.frame_parser import extract_frames, parse_frame_metadata

# Heartbeat frame hex: 59590001000d01015748323432344734303301
HEARTBEAT_HEX = "59590001000d01015748323432344734303301"

# Transparent read request frame
TRANSPARENT_READ_HEX = "59590001001c000257483234323447343033000000000000000811030000003c474b"

# Transparent write frame
TRANSPARENT_WRITE_HEX = "59590001001c00025747323330334732383600000000000000081106001400008b5e"


def test_extract_frames_from_buffer():
    """Single complete heartbeat frame → 1 frame, no remaining bytes."""
    buf = bytes.fromhex(HEARTBEAT_HEX)
    frames, remaining = extract_frames(buf)
    assert len(frames) == 1
    assert frames[0] == buf
    assert remaining == b""


def test_extract_frames_partial():
    """First 10 bytes of a heartbeat → 0 frames, all bytes remain."""
    buf = bytes.fromhex(HEARTBEAT_HEX)[:10]
    frames, remaining = extract_frames(buf)
    assert len(frames) == 0
    assert remaining == buf


def test_extract_frames_multiple():
    """Two heartbeats concatenated → 2 frames extracted."""
    heartbeat = bytes.fromhex(HEARTBEAT_HEX)
    buf = heartbeat + heartbeat
    frames, remaining = extract_frames(buf)
    assert len(frames) == 2
    assert frames[0] == heartbeat
    assert frames[1] == heartbeat
    assert remaining == b""


def test_extract_frames_garbage_prefix():
    """3 garbage bytes before a heartbeat → 1 frame extracted, garbage skipped."""
    garbage = b"\x00\xff\xab"
    heartbeat = bytes.fromhex(HEARTBEAT_HEX)
    buf = garbage + heartbeat
    frames, remaining = extract_frames(buf)
    assert len(frames) == 1
    assert frames[0] == heartbeat


def test_parse_frame_heartbeat():
    """Heartbeat frame parses to correct metadata."""
    frame = bytes.fromhex(HEARTBEAT_HEX)
    meta = parse_frame_metadata(frame)
    assert meta["type"] == "heartbeat"
    assert meta["serial"] == "WH2424G403"
    assert meta["uid"] == 1
    assert meta["adapter_type"] == 1


def test_parse_frame_transparent_read_request():
    """Transparent read-holding-registers frame parses correctly."""
    frame = bytes.fromhex(TRANSPARENT_READ_HEX)
    meta = parse_frame_metadata(frame)
    assert meta["type"] == "transparent"
    assert meta["uid"] == 0
    assert meta["func"] == 0x03
    assert meta["func_name"] == "ReadHR"
    assert meta["addr"] == 0x11


def test_parse_frame_transparent_write():
    """Transparent write-holding-registers frame parses correctly."""
    frame = bytes.fromhex(TRANSPARENT_WRITE_HEX)
    meta = parse_frame_metadata(frame)
    assert meta["type"] == "transparent"
    assert meta["func"] == 0x06
    assert meta["func_name"] == "WriteHR"


def test_parse_frame_short():
    """Frame shorter than 8 bytes returns type='unknown'."""
    frame = b"\x59\x59\x00\x01\x00\x01"  # 6 bytes, missing uid/fid
    meta = parse_frame_metadata(frame)
    assert meta["type"] == "unknown"
