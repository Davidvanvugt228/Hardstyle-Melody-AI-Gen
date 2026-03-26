"""
Tests for Hardstyle MIDI Generator backend.
Covers: MIDI parsing, key detection, generation correctness, trend engine.
"""

import pytest
import io
import json
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.midi_parser import (
    parse_midi, _detect_key, _quantize_notes, get_scale_pitches, SCALES
)
from services.generation_engine import HardstyleGenerationEngine, GenerationConfig
from services.trend_engine import TrendEngine, get_trend_engine


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def create_test_midi_bytes(
    notes=None,
    bpm=160.0,
    notes_spec=None
) -> bytes:
    """Create a simple MIDI file for testing."""
    import pretty_midi
    
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    instrument = pretty_midi.Instrument(program=0)
    
    seconds_per_beat = 60.0 / bpm
    
    if notes_spec is None:
        # Default: A minor bassline (A2, C3, E3, G3)
        notes_spec = [
            (45, 0.0, 0.5),   # A2
            (48, 0.5, 1.0),   # C3
            (52, 1.0, 1.5),   # E3
            (55, 1.5, 2.0),   # G3
            (45, 2.0, 2.5),   # A2
            (48, 2.5, 3.0),   # C3
            (52, 3.0, 3.5),   # E3
            (57, 3.5, 4.0),   # A3
        ] * 2  # 8 bars
    
    for pitch, start_beat, end_beat in notes_spec:
        note = pretty_midi.Note(
            velocity=100,
            pitch=pitch,
            start=start_beat * seconds_per_beat,
            end=end_beat * seconds_per_beat,
        )
        instrument.notes.append(note)
    
    midi.instruments.append(instrument)
    buf = io.BytesIO()
    midi.write(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# MIDI Parser Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMIDIParser:
    
    def test_parse_basic_midi(self):
        """Test that a basic MIDI file parses without errors."""
        midi_bytes = create_test_midi_bytes()
        result = parse_midi(midi_bytes)
        
        assert result is not None
        assert result.bpm > 0
        assert len(result.notes) > 0
        assert result.key_root in range(12)
        assert result.scale_type in SCALES.keys()
    
    def test_bpm_extraction(self):
        """Test BPM is correctly extracted."""
        midi_bytes = create_test_midi_bytes(bpm=160.0)
        result = parse_midi(midi_bytes)
        assert abs(result.bpm - 160.0) < 1.0, f"Expected ~160 BPM, got {result.bpm}"
    
    def test_key_detection_a_minor(self):
        """Test key detection for A minor bassline."""
        # A minor scale: A C D E G
        a_minor_notes = [
            (45, 0.0, 0.5),  # A2
            (48, 0.5, 1.0),  # C3
            (50, 1.0, 1.5),  # D3
            (52, 1.5, 2.0),  # E3
            (55, 2.0, 2.5),  # G3
            (45, 2.5, 3.0),  # A2
            (52, 3.0, 3.5),  # E3
            (45, 3.5, 4.0),  # A2
        ] * 2
        
        midi_bytes = create_test_midi_bytes(notes_spec=a_minor_notes)
        result = parse_midi(midi_bytes)
        
        # Should detect A (pitch class 9) as root
        assert result.key_root == 9, f"Expected A (9), got {result.key_root} ({result.key_name})"
    
    def test_quantization(self):
        """Test that quantized notes land on grid."""
        midi_bytes = create_test_midi_bytes()
        result = parse_midi(midi_bytes)
        
        grid = 1.0 / 4  # 1/16th note = 0.25 beats
        for note in result.quantized_notes:
            remainder = note.start_beat % grid
            assert remainder < 0.01 or remainder > grid - 0.01, \
                f"Note at {note.start_beat} not on 16th grid"
    
    def test_empty_midi_raises(self):
        """Test that empty/invalid data raises ValueError."""
        with pytest.raises((ValueError, Exception)):
            parse_midi(b"not a midi file")
    
    def test_note_count_preserved(self):
        """Test that note count is approximately preserved after parsing."""
        notes_spec = [(45, i * 0.5, i * 0.5 + 0.4) for i in range(16)]
        midi_bytes = create_test_midi_bytes(notes_spec=notes_spec)
        result = parse_midi(midi_bytes)
        assert len(result.notes) == 16


# ─────────────────────────────────────────────────────────────────────────────
# Scale Helper Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestScaleHelpers:
    
    def test_scale_pitches_in_range(self):
        """All scale pitches should be valid MIDI pitches."""
        pitches = get_scale_pitches(9, "natural_minor", octave_range=(3, 6))
        assert all(0 <= p <= 127 for p in pitches)
    
    def test_scale_pitches_correct_intervals(self):
        """Check natural minor intervals are correct."""
        root = 0  # C
        pitches = get_scale_pitches(root, "natural_minor", octave_range=(4, 4))
        pitch_classes = [p % 12 for p in pitches]
        expected_pcs = [0, 2, 3, 5, 7, 8, 10]  # C D Eb F G Ab Bb
        assert pitch_classes == expected_pcs
    
    def test_phrygian_has_b2(self):
        """Phrygian scale should have b2 interval."""
        root = 0  # C
        pitches = get_scale_pitches(root, "phrygian", octave_range=(4, 4))
        pitch_classes = [p % 12 for p in pitches]
        assert 1 in pitch_classes  # Db = b2


# ─────────────────────────────────────────────────────────────────────────────
# Trend Engine Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTrendEngine:
    
    def setup_method(self):
        self.trend = get_trend_engine()
    
    def test_loads_patterns(self):
        """Trend engine should load melody patterns."""
        patterns = self.trend.melody_patterns.get("patterns", [])
        assert len(patterns) > 0, "No melody patterns loaded"
    
    def test_loads_progressions(self):
        """Trend engine should load chord progressions."""
        progressions = self.trend.chord_progressions.get("progressions", [])
        assert len(progressions) > 0, "No chord progressions loaded"
    
    def test_pattern_selection_rawstyle(self):
        """Should select rawstyle patterns."""
        pattern = self.trend.select_melody_pattern(style="rawstyle")
        assert pattern is not None
        assert "id" in pattern
        assert "interval_pattern" in pattern
    
    def test_pattern_selection_euphoric(self):
        """Should select euphoric patterns."""
        pattern = self.trend.select_melody_pattern(style="euphoric")
        assert pattern is not None
    
    def test_weights_positive(self):
        """All computed weights should be positive."""
        patterns = self.trend.melody_patterns.get("patterns", [])
        weights = self.trend._compute_weights(patterns)
        assert all(w > 0 for w in weights), "Found non-positive weight"
    
    def test_bpm_style_detection(self):
        """BPM style detection should return valid styles."""
        slow = self.trend.detect_style_from_bpm(152)
        fast = self.trend.detect_style_from_bpm(168)
        assert slow in ["rawstyle", "euphoric"]
        assert fast in ["rawstyle", "euphoric"]
    
    def test_trend_summary_structure(self):
        """Trend summary should have required fields."""
        summary = self.trend.get_trend_summary()
        assert "version" in summary
        assert "top_patterns" in summary
        assert "available_styles" in summary


# ─────────────────────────────────────────────────────────────────────────────
# Generation Engine Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerationEngine:
    
    def setup_method(self):
        self.trend = get_trend_engine()
        self.engine = HardstyleGenerationEngine(self.trend)
        self.midi_bytes = create_test_midi_bytes(bpm=160.0)
        self.parsed = parse_midi(self.midi_bytes)
    
    def test_generate_returns_all_parts(self):
        """Generation should return lead, chords, and pads."""
        config = GenerationConfig(style="rawstyle", energy="aggressive", bars=4)
        result = self.engine.generate(self.parsed, config)
        
        assert result.lead is not None and len(result.lead) > 0
        assert result.chords is not None and len(result.chords) > 0
        assert result.pads is not None and len(result.pads) > 0
    
    def test_generated_midi_is_valid(self):
        """Generated MIDI should be parseable by pretty_midi."""
        import pretty_midi
        
        config = GenerationConfig(style="rawstyle", energy="aggressive", bars=4)
        result = self.engine.generate(self.parsed, config)
        
        for part_name, part_bytes in [("lead", result.lead), ("chords", result.chords), ("pads", result.pads)]:
            midi_obj = pretty_midi.PrettyMIDI(io.BytesIO(part_bytes))
            assert len(midi_obj.instruments) > 0, f"{part_name} has no instruments"
            assert len(midi_obj.instruments[0].notes) > 0, f"{part_name} has no notes"
    
    def test_lead_pitches_in_scale(self):
        """Lead notes should be in the detected scale."""
        import pretty_midi
        
        config = GenerationConfig(style="rawstyle", energy="aggressive", bars=4)
        result = self.engine.generate(self.parsed, config)
        
        scale_pitches = get_scale_pitches(
            self.parsed.key_root, self.parsed.scale_type, octave_range=(0, 10)
        )
        scale_pcs = set(p % 12 for p in scale_pitches)
        
        lead_midi = pretty_midi.PrettyMIDI(io.BytesIO(result.lead))
        for note in lead_midi.instruments[0].notes:
            assert note.pitch % 12 in scale_pcs, \
                f"Note {note.pitch} (pc={note.pitch%12}) not in scale {self.parsed.key_name}"
    
    def test_metadata_structure(self):
        """Generation metadata should have required fields."""
        config = GenerationConfig(style="euphoric", energy="high", bars=4)
        result = self.engine.generate(self.parsed, config)
        
        assert "bpm" in result.metadata
        assert "key" in result.metadata
        assert "style" in result.metadata
        assert result.metadata["style"] == "euphoric"
    
    def test_euphoric_generation(self):
        """Euphoric style should generate valid MIDI."""
        config = GenerationConfig(style="euphoric", energy="high", bars=4)
        result = self.engine.generate(self.parsed, config)
        assert len(result.lead) > 0
    
    def test_no_overlapping_notes_same_pitch(self):
        """Generated MIDI should not have overlapping notes on same pitch."""
        import pretty_midi
        
        config = GenerationConfig(style="rawstyle", energy="dark", bars=8)
        result = self.engine.generate(self.parsed, config)
        
        lead_midi = pretty_midi.PrettyMIDI(io.BytesIO(result.lead))
        notes = sorted(lead_midi.instruments[0].notes, key=lambda n: (n.pitch, n.start))
        
        # Check no same-pitch overlap
        pitch_groups = {}
        for note in notes:
            if note.pitch not in pitch_groups:
                pitch_groups[note.pitch] = []
            pitch_groups[note.pitch].append(note)
        
        for pitch, pitch_notes in pitch_groups.items():
            for i in range(len(pitch_notes) - 1):
                assert pitch_notes[i].end <= pitch_notes[i+1].start + 0.001, \
                    f"Overlapping notes on pitch {pitch}"
    
    def test_generation_deterministic_with_seed(self):
        """Same seed should produce same output."""
        config1 = GenerationConfig(style="rawstyle", energy="aggressive", bars=4, variation_seed=42)
        config2 = GenerationConfig(style="rawstyle", energy="aggressive", bars=4, variation_seed=42)
        
        result1 = self.engine.generate(self.parsed, config1)
        result2 = self.engine.generate(self.parsed, config2)
        
        assert result1.lead == result2.lead


# ─────────────────────────────────────────────────────────────────────────────
# Trend Data Integrity Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTrendDataIntegrity:
    
    def test_melody_patterns_have_required_fields(self):
        """All melody patterns must have required fields."""
        trend = get_trend_engine()
        required = ["id", "style", "weight", "recency_score", "interval_pattern", "rhythm_pattern"]
        
        for pattern in trend.melody_patterns.get("patterns", []):
            for field in required:
                assert field in pattern, f"Pattern {pattern.get('id')} missing field: {field}"
    
    def test_weights_in_valid_range(self):
        """Weights should be between 0 and 1."""
        trend = get_trend_engine()
        for pattern in trend.melody_patterns.get("patterns", []):
            assert 0 < pattern["weight"] <= 1.0
            assert 0 < pattern["recency_score"] <= 1.0
    
    def test_chord_progressions_have_degrees(self):
        """Chord progressions must have degree lists."""
        trend = get_trend_engine()
        for prog in trend.chord_progressions.get("progressions", []):
            assert "degrees" in prog
            assert len(prog["degrees"]) >= 2
    
    def test_genre_profiles_exist(self):
        """Both rawstyle and euphoric profiles must exist."""
        trend = get_trend_engine()
        profiles = trend.genre_profiles.get("profiles", {})
        assert "rawstyle" in profiles
        assert "euphoric" in profiles


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
