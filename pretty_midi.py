"""
Minimal pretty_midi-compatible implementation for offline environments.
Implements the subset used by this project: PrettyMIDI, Instrument, Note.
Uses Python's built-in struct for MIDI byte manipulation.
"""

import struct
import io
import math


class Note:
    def __init__(self, velocity: int, pitch: int, start: float, end: float):
        self.velocity = int(velocity)
        self.pitch = int(pitch)
        self.start = float(start)
        self.end = float(end)

    def __repr__(self):
        return f"Note(pitch={self.pitch}, vel={self.velocity}, start={self.start:.3f}, end={self.end:.3f})"


class Instrument:
    def __init__(self, program: int = 0, is_drum: bool = False, name: str = ""):
        self.program = program
        self.is_drum = is_drum
        self.name = name
        self.notes: list[Note] = []


class TimeSignature:
    def __init__(self, numerator: int, denominator: int, time: float = 0.0):
        self.numerator = numerator
        self.denominator = denominator
        self.time = time


class PrettyMIDI:
    TICKS_PER_BEAT = 480

    def __init__(self, midi_file=None, initial_tempo: float = 120.0):
        self.instruments: list[Instrument] = []
        self.time_signature_changes: list[TimeSignature] = [TimeSignature(4, 4, 0.0)]
        self._initial_tempo = initial_tempo
        self._tempo_change_times = [0.0]
        self._tempo_change_bpms = [initial_tempo]

        if midi_file is not None:
            self._parse(midi_file)

    # ── Tempo API ──────────────────────────────────────────────────────────

    def get_tempo_changes(self):
        return (self._tempo_change_times, self._tempo_change_bpms)

    # ── Parse ──────────────────────────────────────────────────────────────

    def _parse(self, source):
        if hasattr(source, 'read'):
            data = source.read()
        else:
            data = source

        pos = 0

        # MThd header
        if data[pos:pos+4] != b'MThd':
            raise ValueError("Not a MIDI file")
        pos += 4
        header_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4
        fmt = struct.unpack('>H', data[pos:pos+2])[0]; pos += 2
        num_tracks = struct.unpack('>H', data[pos:pos+2])[0]; pos += 2
        ticks = struct.unpack('>H', data[pos:pos+2])[0]; pos += 2

        tpb = ticks  # ticks per beat

        # Parse tracks
        tempo = 500000  # 120 BPM in microseconds
        detected_tempo = None

        for track_idx in range(num_tracks):
            if pos + 8 > len(data):
                break
            if data[pos:pos+4] != b'MTrk':
                break
            pos += 4
            track_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4
            track_end = pos + track_len

            instrument = Instrument(program=0, is_drum=(track_idx == 9))
            active_notes: dict[int, tuple[int, int, int]] = {}  # pitch -> (start_tick, velocity, channel)
            current_tick = 0
            running_status = 0

            track_data = data[pos:track_end]
            tp = 0

            def read_var(d, p):
                value = 0
                while True:
                    b = d[p]; p += 1
                    value = (value << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break
                return value, p

            while tp < len(track_data):
                delta, tp = read_var(track_data, tp)
                current_tick += delta

                if tp >= len(track_data):
                    break

                status = track_data[tp]

                # Running status or new status
                if status & 0x80:
                    running_status = status
                    tp += 1
                else:
                    status = running_status

                event_type = status & 0xF0
                channel = status & 0x0F

                if event_type == 0x90:  # Note On
                    pitch = track_data[tp]; tp += 1
                    vel = track_data[tp]; tp += 1
                    if vel > 0:
                        active_notes[pitch] = (current_tick, vel, channel)
                    else:
                        if pitch in active_notes:
                            start_tick, vel2, _ = active_notes.pop(pitch)
                            start_sec = start_tick / tpb * (tempo / 1e6)
                            end_sec = current_tick / tpb * (tempo / 1e6)
                            instrument.notes.append(Note(vel2, pitch, start_sec, end_sec))

                elif event_type == 0x80:  # Note Off
                    pitch = track_data[tp]; tp += 1
                    tp += 1  # velocity
                    if pitch in active_notes:
                        start_tick, vel2, _ = active_notes.pop(pitch)
                        start_sec = start_tick / tpb * (tempo / 1e6)
                        end_sec = current_tick / tpb * (tempo / 1e6)
                        instrument.notes.append(Note(vel2, pitch, start_sec, end_sec))

                elif event_type == 0xC0:  # Program Change
                    prog = track_data[tp]; tp += 1
                    instrument.program = prog

                elif event_type == 0xA0:  # Aftertouch
                    tp += 2

                elif event_type == 0xB0:  # Control Change
                    tp += 2

                elif event_type == 0xE0:  # Pitch Bend
                    tp += 2

                elif event_type == 0xF0:
                    if status == 0xFF:  # Meta
                        meta_type = track_data[tp]; tp += 1
                        meta_len, tp = read_var(track_data, tp)
                        meta_data = track_data[tp:tp+meta_len]; tp += meta_len

                        if meta_type == 0x51:  # Tempo
                            tempo = struct.unpack('>I', b'\x00' + meta_data)[0]
                            bpm = 60e6 / tempo
                            if detected_tempo is None:
                                detected_tempo = bpm
                                self._initial_tempo = bpm
                                self._tempo_change_bpms = [bpm]

                        elif meta_type == 0x58:  # Time Signature
                            num = meta_data[0]
                            den = 2 ** meta_data[1]
                            self.time_signature_changes = [TimeSignature(num, den, 0.0)]

                    elif status == 0xF0:  # SysEx
                        while tp < len(track_data) and track_data[tp] != 0xF7:
                            tp += 1
                        tp += 1
                    else:
                        tp += 1

                else:
                    tp += 1

            # Close unclosed notes
            for pitch, (start_tick, vel, _) in active_notes.items():
                start_sec = start_tick / tpb * (tempo / 1e6)
                end_sec = (current_tick + tpb) / tpb * (tempo / 1e6)
                instrument.notes.append(Note(vel, pitch, start_sec, end_sec))

            if instrument.notes:
                self.instruments.append(instrument)

            pos = track_end

    # ── Write ──────────────────────────────────────────────────────────────

    def write(self, target):
        tpb = self.TICKS_PER_BEAT
        bpm = self._initial_tempo
        uspb = int(60e6 / bpm)

        def var_len(value):
            buf = []
            buf.append(value & 0x7F)
            value >>= 7
            while value:
                buf.append((value & 0x7F) | 0x80)
                value >>= 7
            return bytes(reversed(buf))

        tracks = []
        # Tempo track
        tempo_track = io.BytesIO()
        # Tempo meta event at tick 0
        tempo_track.write(var_len(0))          # delta time = 0
        tempo_track.write(bytes([0xFF, 0x51, 0x03]))
        tempo_track.write(struct.pack('>I', uspb)[1:])  # 3 bytes
        # Time signature 4/4
        tempo_track.write(var_len(0))
        tempo_track.write(bytes([0xFF, 0x58, 0x04, 0x04, 0x02, 0x18, 0x08]))
        # End of track
        tempo_track.write(bytes([0x00, 0xFF, 0x2F, 0x00]))
        tracks.append(tempo_track.getvalue())

        # Instrument tracks
        for instrument in self.instruments:
            buf = io.BytesIO()
            events = []

            for note in instrument.notes:
                start_tick = int(round(note.start * bpm / 60 * tpb))
                end_tick = int(round(note.end * bpm / 60 * tpb))
                end_tick = max(end_tick, start_tick + 1)
                events.append((start_tick, 0x90, note.pitch, note.velocity))
                events.append((end_tick, 0x80, note.pitch, 0))

            # Program change at tick 0
            if not instrument.is_drum:
                events.append((0, 0xC0, instrument.program, -1))

            events.sort(key=lambda e: (e[0], e[1]))

            last_tick = 0
            for tick, status, data1, data2 in events:
                delta = tick - last_tick
                last_tick = tick
                buf.write(var_len(max(0, delta)))
                if data2 == -1:
                    buf.write(bytes([status, data1]))
                else:
                    buf.write(bytes([status, data1, data2]))

            buf.write(bytes([0x00, 0xFF, 0x2F, 0x00]))
            tracks.append(buf.getvalue())

        # Assemble MIDI file
        out = io.BytesIO()
        # MThd
        out.write(b'MThd')
        out.write(struct.pack('>I', 6))
        out.write(struct.pack('>H', 1 if len(tracks) > 1 else 0))  # format
        out.write(struct.pack('>H', len(tracks)))
        out.write(struct.pack('>H', tpb))

        for track in tracks:
            out.write(b'MTrk')
            out.write(struct.pack('>I', len(track)))
            out.write(track)

        out.seek(0)
        target.write(out.read())
