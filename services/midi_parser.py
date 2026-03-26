"""
MIDI Parser Service
Extracts musical information from uploaded bassline MIDI files.
Detects key, BPM, note patterns, and normalizes timing.
"""

import pretty_midi
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class ParsedNote:
    pitch: int
    velocity: int
    start_beat: float
    end_beat: float
    duration_beats: float


@dataclass 
class ParsedMIDI:
    bpm: float
    time_signature_numerator: int
    time_signature_denominator: int
    key_root: int          # MIDI note number of key root (0-11)
    key_name: str          # e.g. "A minor"
    scale_type: str        # "minor", "major", "phrygian", "harmonic_minor"
    notes: List[ParsedNote]
    total_bars: int
    beats_per_bar: int
    quantized_notes: List[ParsedNote]


# Scale definitions: intervals from root
SCALES = {
    "natural_minor":   [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor":  [0, 2, 3, 5, 7, 8, 11],
    "phrygian":        [0, 1, 3, 5, 7, 8, 10],
    "dorian":          [0, 2, 3, 5, 7, 9, 10],
    "major":           [0, 2, 4, 5, 7, 9, 11],
    "minor_pentatonic":[0, 3, 5, 7, 10],
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def parse_midi(midi_bytes: bytes) -> ParsedMIDI:
    """
    Main entry point: parse raw MIDI bytes into structured musical data.
    """
    import io
    midi = pretty_midi.PrettyMIDI(io.BytesIO(midi_bytes))
    
    bpm = _extract_bpm(midi)
    ts_num, ts_denom = _extract_time_signature(midi)
    notes = _extract_notes(midi, bpm)
    
    if not notes:
        raise ValueError("No notes found in MIDI file")
    
    key_root, scale_type = _detect_key(notes)
    key_name = f"{NOTE_NAMES[key_root]} {scale_type.replace('_', ' ')}"
    
    total_beats = max(n.end_beat for n in notes)
    beats_per_bar = ts_num
    total_bars = math.ceil(total_beats / beats_per_bar)
    
    quantized = _quantize_notes(notes, subdivision=16)
    
    return ParsedMIDI(
        bpm=bpm,
        time_signature_numerator=ts_num,
        time_signature_denominator=ts_denom,
        key_root=key_root,
        key_name=key_name,
        scale_type=scale_type,
        notes=notes,
        total_bars=max(total_bars, 4),
        beats_per_bar=beats_per_bar,
        quantized_notes=quantized,
    )


def _extract_bpm(midi: pretty_midi.PrettyMIDI) -> float:
    """Extract BPM, defaulting to 160 for hardstyle."""
    tempos = midi.get_tempo_changes()
    if len(tempos[1]) > 0:
        bpm = float(tempos[1][0])
        # Clamp to reasonable hardstyle range
        if bpm < 60:
            bpm *= 2
        if bpm > 200:
            bpm /= 2
        return round(bpm, 2)
    return 160.0


def _extract_time_signature(midi: pretty_midi.PrettyMIDI) -> Tuple[int, int]:
    """Extract time signature, defaulting to 4/4."""
    for ts in midi.time_signature_changes:
        return ts.numerator, ts.denominator
    return 4, 4


def _extract_notes(midi: pretty_midi.PrettyMIDI, bpm: float) -> List[ParsedNote]:
    """Extract notes from all tracks, converting to beat positions."""
    notes = []
    seconds_per_beat = 60.0 / bpm
    
    for instrument in midi.instruments:
        if instrument.is_drum:
            continue
        for note in instrument.notes:
            start_beat = note.start / seconds_per_beat
            end_beat = note.end / seconds_per_beat
            notes.append(ParsedNote(
                pitch=note.pitch,
                velocity=note.velocity,
                start_beat=round(start_beat, 4),
                end_beat=round(end_beat, 4),
                duration_beats=round(end_beat - start_beat, 4),
            ))
    
    return sorted(notes, key=lambda n: n.start_beat)


def _detect_key(notes: List[ParsedNote]) -> Tuple[int, str]:
    """
    Detect key using Krumhansl-Schmuckler key-finding algorithm.
    Returns (root_pitch_class, scale_type).
    """
    # Key profiles (Krumhansl-Schmuckler)
    major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    
    # Count pitch class usage weighted by duration
    pitch_counts = np.zeros(12)
    for note in notes:
        pc = note.pitch % 12
        pitch_counts[pc] += note.duration_beats
    
    if pitch_counts.sum() == 0:
        return 9, "natural_minor"  # A minor default
    
    # Correlate with each key
    best_key = 0
    best_scale = "natural_minor"
    best_score = -np.inf
    
    for root in range(12):
        # Rotate profiles to this root
        rotated_major = np.roll(major_profile, root)
        rotated_minor = np.roll(minor_profile, root)
        
        score_major = np.corrcoef(pitch_counts, rotated_major)[0, 1]
        score_minor = np.corrcoef(pitch_counts, rotated_minor)[0, 1]
        
        if score_major > best_score:
            best_score = score_major
            best_key = root
            best_scale = "major"
        
        if score_minor > best_score:
            best_score = score_minor
            best_key = root
            best_scale = "natural_minor"
    
    # For hardstyle: if major detected, bias toward relative minor
    if best_scale == "major":
        relative_minor = (best_key + 9) % 12
        # Check if the music sounds more minor (lower notes emphasized)
        avg_pitch = np.mean([n.pitch for n in notes])
        if avg_pitch < 60:  # Low register suggests rawstyle/minor
            best_key = relative_minor
            best_scale = "natural_minor"
    
    # Check for phrygian (common in rawstyle - b2 interval prominent)
    b2_pc = (best_key + 1) % 12
    if pitch_counts[b2_pc] > pitch_counts.mean() * 1.5:
        best_scale = "phrygian"
    
    # Check for harmonic minor (common in euphoric hardstyle)
    leading_tone = (best_key + 11) % 12
    if best_scale == "natural_minor" and pitch_counts[leading_tone] > pitch_counts.mean():
        best_scale = "harmonic_minor"
    
    return best_key, best_scale


def _quantize_notes(notes: List[ParsedNote], subdivision: int = 16) -> List[ParsedNote]:
    """
    Quantize note start times to the nearest subdivision of a beat.
    subdivision=16 means 1/16th note grid.
    """
    grid = 1.0 / (subdivision / 4)  # Grid size in beats
    quantized = []
    
    for note in notes:
        q_start = round(note.start_beat / grid) * grid
        q_dur = max(grid, round(note.duration_beats / grid) * grid)
        quantized.append(ParsedNote(
            pitch=note.pitch,
            velocity=note.velocity,
            start_beat=q_start,
            end_beat=q_start + q_dur,
            duration_beats=q_dur,
        ))
    
    return quantized


def get_pitch_classes_from_notes(notes: List[ParsedNote]) -> List[int]:
    """Get unique pitch classes from note list."""
    return list(set(n.pitch % 12 for n in notes))


def get_scale_pitches(root: int, scale_type: str, octave_range: Tuple[int, int] = (3, 6)) -> List[int]:
    """
    Get all MIDI pitches in the given scale within octave range.
    """
    intervals = SCALES.get(scale_type, SCALES["natural_minor"])
    pitches = []
    for octave in range(octave_range[0], octave_range[1] + 1):
        for interval in intervals:
            pitch = (octave + 1) * 12 + root + interval
            if 0 <= pitch <= 127:
                pitches.append(pitch)
    return sorted(pitches)


def analyze_bassline_pattern(notes: List[ParsedNote]) -> Dict:
    """
    Analyze the bassline for pattern characteristics.
    Returns structural info useful for generation.
    """
    if not notes:
        return {}
    
    pitches = [n.pitch for n in notes]
    intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
    
    # Detect rhythmic emphasis (which beats have notes)
    beat_hits = set()
    for note in notes:
        beat = round(note.start_beat * 4) / 4  # Quantize to 16th
        beat_hits.add(beat % 4)  # Within 1 bar
    
    return {
        "pitch_range": max(pitches) - min(pitches),
        "avg_pitch": sum(pitches) / len(pitches),
        "lowest_pitch": min(pitches),
        "highest_pitch": max(pitches),
        "interval_avg": sum(abs(i) for i in intervals) / len(intervals) if intervals else 0,
        "beat_hits": sorted(beat_hits),
        "note_count": len(notes),
        "rhythmic_density": len(notes) / max(n.end_beat for n in notes) if notes else 0,
    }
