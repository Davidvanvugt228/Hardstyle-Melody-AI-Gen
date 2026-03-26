"""
Hardstyle/Rawstyle MIDI Generation Engine
Hybrid system: Rule-based + Trend-based + Variation layers.
Generates musically coherent leads, chords, and pads.
"""

import pretty_midi
import numpy as np
import random
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .midi_parser import (
    ParsedMIDI, ParsedNote, SCALES, get_scale_pitches, analyze_bassline_pattern
)
from .trend_engine import TrendEngine


@dataclass
class GenerationConfig:
    style: str = "rawstyle"          # rawstyle, euphoric
    energy: str = "aggressive"       # dark, aggressive, medium, high
    bars: int = 8
    subdivision: int = 16
    variation_seed: Optional[int] = None


@dataclass
class GeneratedMIDI:
    lead: bytes
    chords: bytes
    pads: bytes
    metadata: Dict
    pattern_ids_used: List[str]


class HardstyleGenerationEngine:
    """
    Core generation engine implementing hybrid rule-based + trend-informed generation.
    
    Architecture:
    A. Rule-Based Layer: Harmonic correctness, key adherence, phrasing
    B. Trend-Based Layer: Pattern selection via TrendEngine
    C. Variation Engine: Prevents loops, adds expressiveness
    """
    
    def __init__(self, trend_engine: TrendEngine):
        self.trend = trend_engine
        
    def generate(self, parsed_midi: ParsedMIDI, config: GenerationConfig) -> GeneratedMIDI:
        """
        Main generation method. Takes parsed bassline, returns three MIDI files.
        """
        if config.variation_seed is not None:
            random.seed(config.variation_seed)
            np.random.seed(config.variation_seed)
        
        # A. Analyze bassline structure
        bassline_analysis = analyze_bassline_pattern(parsed_midi.quantized_notes)
        
        # B. Get genre profile for this style
        profile = self.trend.get_genre_profile(config.style)
        
        # C. Select patterns from trend engine
        melody_pattern = self.trend.select_melody_pattern(
            style=config.style, 
            energy=config.energy
        )
        chord_prog = self.trend.select_chord_progression(style=config.style)
        
        # D. Generate each element
        lead_notes = self._generate_lead(
            parsed_midi, config, melody_pattern, bassline_analysis, profile
        )
        chord_notes = self._generate_chords(
            parsed_midi, config, chord_prog, profile
        )
        pad_notes = self._generate_pads(
            parsed_midi, config, chord_prog, profile
        )
        
        # E. Render to MIDI bytes
        lead_bytes = self._render_midi(lead_notes, parsed_midi.bpm, program=80)   # Synth Lead
        chord_bytes = self._render_midi(chord_notes, parsed_midi.bpm, program=89) # Pad 2 (warm)
        pad_bytes = self._render_midi(pad_notes, parsed_midi.bpm, program=91)     # Pad 4 (choir)
        
        return GeneratedMIDI(
            lead=lead_bytes,
            chords=chord_bytes,
            pads=pad_bytes,
            metadata={
                "bpm": parsed_midi.bpm,
                "key": parsed_midi.key_name,
                "scale": parsed_midi.scale_type,
                "style": config.style,
                "energy": config.energy,
                "bars_generated": config.bars,
                "melody_pattern": melody_pattern["id"],
                "chord_progression": chord_prog["id"],
            },
            pattern_ids_used=[melody_pattern["id"], chord_prog["id"]]
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # LEAD GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    
    def _generate_lead(
        self,
        parsed: ParsedMIDI,
        config: GenerationConfig,
        pattern: Dict,
        bassline: Dict,
        profile: Dict
    ) -> List[ParsedNote]:
        """
        Generate lead melody using trend pattern + harmonic rules.
        Implements 2-bar and 4-bar phrasing typical of hardstyle.
        """
        scale_pitches = get_scale_pitches(
            parsed.key_root, 
            parsed.scale_type, 
            octave_range=(4, 6)
        )
        
        if not scale_pitches:
            scale_pitches = get_scale_pitches(parsed.key_root, "natural_minor", (4, 6))
        
        lead_profile = profile.get("lead_characteristics", {})
        velocity_range = lead_profile.get("velocity_range", [85, 110])
        phrase_bars = random.choice(lead_profile.get("phrase_length_bars", [2, 4]))
        
        notes = []
        interval_pattern = pattern["interval_pattern"]
        rhythm_pattern = pattern["rhythm_pattern"]
        
        # Grid: 16th note resolution
        step_size = 1.0 / (config.subdivision / 4)  # In beats (1/4 = 1 beat)
        steps_per_bar = config.subdivision  # 16 steps per bar
        
        # Root pitch: in lead range, above bassline
        bassline_avg = bassline.get("avg_pitch", 48)
        root_candidate = self._find_nearest_scale_pitch(
            max(bassline_avg + 12, 60),  # At least an octave above bassline
            scale_pitches
        )
        
        current_pitch = root_candidate
        pattern_len = len(interval_pattern)
        
        # Generate phrase by phrase
        for bar in range(config.bars):
            phrase_position = bar % phrase_bars
            
            for step in range(steps_per_bar):
                global_step = bar * steps_per_bar + step
                pattern_step = global_step % len(rhythm_pattern)
                
                if not rhythm_pattern[pattern_step]:
                    continue
                
                # Apply interval pattern
                interval_idx = (global_step // 2) % pattern_len
                interval = interval_pattern[interval_idx]
                
                # Find target pitch
                target_pitch = current_pitch + interval
                nearest = self._find_nearest_scale_pitch(target_pitch, scale_pitches)
                
                # Variation: octave jumps
                if self._should_octave_jump(bar, step, config.style):
                    direction = 1 if random.random() > 0.5 else -1
                    octave_candidate = nearest + (12 * direction)
                    if 48 <= octave_candidate <= 96:
                        nearest = octave_candidate
                
                # Phrase ending: resolve to root or 5th
                is_phrase_end = (step >= steps_per_bar - 4) and (phrase_position == phrase_bars - 1)
                if is_phrase_end:
                    nearest = self._resolve_to_scale_degree(
                        nearest, parsed.key_root, scale_pitches, degree=1
                    )
                
                # Duration: tied to next hit or short stab
                next_hit = self._find_next_hit(global_step, rhythm_pattern)
                duration = step_size * next_hit * 0.9  # 10% gap for articulation
                
                velocity = self._humanize_velocity(
                    velocity_range[0], velocity_range[1],
                    step == 0, bar % 2 == 0
                )
                
                start_beat = global_step * step_size
                notes.append(ParsedNote(
                    pitch=nearest,
                    velocity=velocity,
                    start_beat=start_beat,
                    end_beat=start_beat + max(duration, step_size),
                    duration_beats=max(duration, step_size),
                ))
                
                current_pitch = nearest
        
        # Apply variation layer
        notes = self._apply_lead_variations(notes, parsed, config)
        return notes
    
    # ─────────────────────────────────────────────────────────────────────────
    # CHORD GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    
    def _generate_chords(
        self,
        parsed: ParsedMIDI,
        config: GenerationConfig,
        progression: Dict,
        profile: Dict
    ) -> List[ParsedNote]:
        """
        Generate chord stabs/hits based on progression.
        Rawstyle: short stabs, sparse. Euphoric: sustained lush chords.
        """
        chord_profile = profile.get("chord_characteristics", {})
        is_stab = chord_profile.get("style") == "power_stabs"
        
        scale_intervals = SCALES.get(parsed.scale_type, SCALES["natural_minor"])
        degrees = progression.get("degrees", [1, 6, 3, 7])
        qualities = progression.get("quality", ["minor", "major", "minor", "major"])
        
        notes = []
        bars_per_chord = max(1, config.bars // len(degrees))
        
        step_size = 1.0 / (config.subdivision / 4)
        
        for chord_idx, (degree, quality) in enumerate(zip(degrees, qualities)):
            # Get chord root from scale
            degree_interval = scale_intervals[(degree - 1) % len(scale_intervals)]
            chord_root_pitch = (4 * 12) + parsed.key_root + degree_interval  # Octave 4
            
            # Build chord voicing
            chord_pitches = self._build_chord(chord_root_pitch, quality, chord_profile)
            
            bar_start = chord_idx * bars_per_chord
            bar_end = min(bar_start + bars_per_chord, config.bars)
            
            for bar in range(bar_start, bar_end):
                if is_stab:
                    # Rawstyle: stabs on beat 1, sometimes beat 3
                    stab_positions = self._get_stab_positions(bar, config)
                    for pos_beat in stab_positions:
                        stab_dur = step_size * 2  # Short stab
                        for pitch in chord_pitches:
                            velocity = random.randint(85, 105)
                            notes.append(ParsedNote(
                                pitch=pitch,
                                velocity=velocity,
                                start_beat=pos_beat,
                                end_beat=pos_beat + stab_dur,
                                duration_beats=stab_dur,
                            ))
                else:
                    # Euphoric: sustained chord per bar
                    dur = 4.0 * bars_per_chord * 0.95  # Almost full duration
                    for pitch in chord_pitches:
                        velocity = random.randint(70, 90)
                        notes.append(ParsedNote(
                            pitch=pitch,
                            velocity=velocity,
                            start_beat=bar * 4.0,
                            end_beat=bar * 4.0 + dur,
                            duration_beats=dur,
                        ))
        
        return notes
    
    # ─────────────────────────────────────────────────────────────────────────
    # PAD GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    
    def _generate_pads(
        self,
        parsed: ParsedMIDI,
        config: GenerationConfig,
        progression: Dict,
        profile: Dict
    ) -> List[ParsedNote]:
        """
        Generate atmospheric pads - long sustained notes creating harmonic bed.
        Uses wide voicings, slow attack feel implied by long notes.
        """
        pad_profile = profile.get("pad_characteristics", {})
        preferred_intervals = pad_profile.get("preferred_intervals", [0, 7, 12])
        
        scale_intervals = SCALES.get(parsed.scale_type, SCALES["natural_minor"])
        degrees = progression.get("degrees", [1, 6, 3, 7])
        
        notes = []
        bars_per_section = max(2, config.bars // len(degrees))
        
        for chord_idx, degree in enumerate(degrees):
            degree_interval = scale_intervals[(degree - 1) % len(scale_intervals)]
            pad_root = (3 * 12) + parsed.key_root + degree_interval  # Lower octave for pads
            
            bar_start = chord_idx * bars_per_section
            duration_beats = bars_per_section * 4.0
            
            if bar_start >= config.bars:
                break
            
            # Build wide pad voicing
            for interval in preferred_intervals:
                pitch = pad_root + interval
                if 36 <= pitch <= 84:
                    # Slight velocity variation between pad notes
                    velocity = random.randint(55, 75)
                    # Stagger note starts slightly for organic feel
                    start_offset = random.uniform(0, 0.05)
                    
                    notes.append(ParsedNote(
                        pitch=pitch,
                        velocity=velocity,
                        start_beat=bar_start * 4.0 + start_offset,
                        end_beat=bar_start * 4.0 + duration_beats,
                        duration_beats=duration_beats,
                    ))
        
        return notes
    
    # ─────────────────────────────────────────────────────────────────────────
    # VARIATION ENGINE
    # ─────────────────────────────────────────────────────────────────────────
    
    def _apply_lead_variations(
        self, 
        notes: List[ParsedNote], 
        parsed: ParsedMIDI,
        config: GenerationConfig
    ) -> List[ParsedNote]:
        """
        Apply variation layers to prevent repetition loops.
        - Bar 5-8 variations (second half)
        - Rhythmic variations
        - Velocity humanization
        """
        if len(notes) < 4:
            return notes
        
        total_beats = config.bars * 4.0
        varied = []
        
        for note in notes:
            n = ParsedNote(
                pitch=note.pitch,
                velocity=note.velocity,
                start_beat=note.start_beat,
                end_beat=note.end_beat,
                duration_beats=note.duration_beats,
            )
            
            # Second half: add variations
            if note.start_beat > total_beats / 2:
                # Occasional pitch variation (neighboring scale tone)
                if random.random() < 0.15:
                    scale_pitches = get_scale_pitches(parsed.key_root, parsed.scale_type, (4, 6))
                    idx = self._find_scale_index(n.pitch, scale_pitches)
                    if idx >= 0:
                        # Move up or down by one scale step
                        shift = random.choice([-1, 1])
                        new_idx = max(0, min(len(scale_pitches)-1, idx + shift))
                        n = ParsedNote(
                            pitch=scale_pitches[new_idx],
                            velocity=n.velocity,
                            start_beat=n.start_beat,
                            end_beat=n.end_beat,
                            duration_beats=n.duration_beats,
                        )
                
                # Velocity variation for energy
                if config.energy in ["aggressive", "dark"]:
                    n = ParsedNote(
                        pitch=n.pitch,
                        velocity=min(127, n.velocity + random.randint(0, 10)),
                        start_beat=n.start_beat,
                        end_beat=n.end_beat,
                        duration_beats=n.duration_beats,
                    )
            
            varied.append(n)
        
        return varied
    
    # ─────────────────────────────────────────────────────────────────────────
    # MIDI RENDERING
    # ─────────────────────────────────────────────────────────────────────────
    
    def _render_midi(
        self, 
        notes: List[ParsedNote], 
        bpm: float,
        program: int = 0
    ) -> bytes:
        """
        Render ParsedNote list to MIDI bytes.
        Clean output: quantized, no overlaps, FL Studio ready.
        """
        import io
        midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
        instrument = pretty_midi.Instrument(program=program)
        
        seconds_per_beat = 60.0 / bpm
        
        # Sort and deduplicate by removing overlapping notes on same pitch
        notes_sorted = sorted(notes, key=lambda n: (n.start_beat, n.pitch))
        active: Dict[int, float] = {}  # pitch -> end_beat
        
        for note in notes_sorted:
            start_sec = note.start_beat * seconds_per_beat
            end_sec = note.end_beat * seconds_per_beat
            
            # Trim if overlapping on same pitch
            if note.pitch in active and active[note.pitch] > note.start_beat:
                start_sec = active[note.pitch] * seconds_per_beat
                if start_sec >= end_sec:
                    continue
            
            active[note.pitch] = note.end_beat
            
            pm_note = pretty_midi.Note(
                velocity=int(np.clip(note.velocity, 1, 127)),
                pitch=int(np.clip(note.pitch, 0, 127)),
                start=start_sec,
                end=end_sec,
            )
            instrument.notes.append(pm_note)
        
        midi.instruments.append(instrument)
        
        buf = io.BytesIO()
        midi.write(buf)
        return buf.getvalue()
    
    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _find_nearest_scale_pitch(self, target: int, scale_pitches: List[int]) -> int:
        """Find the scale pitch nearest to target."""
        if not scale_pitches:
            return target
        return min(scale_pitches, key=lambda p: abs(p - target))
    
    def _find_scale_index(self, pitch: int, scale_pitches: List[int]) -> int:
        """Find index of pitch in scale_pitches, or -1."""
        try:
            return scale_pitches.index(pitch)
        except ValueError:
            # Find nearest
            if not scale_pitches:
                return -1
            nearest = self._find_nearest_scale_pitch(pitch, scale_pitches)
            return scale_pitches.index(nearest)
    
    def _resolve_to_scale_degree(
        self, 
        current: int, 
        key_root: int, 
        scale_pitches: List[int],
        degree: int = 1
    ) -> int:
        """Resolve pitch to a specific scale degree (1=root, 5=fifth)."""
        degree_map = {1: 0, 5: 7, 3: 4}
        target_interval = degree_map.get(degree, 0)
        target_pc = (key_root + target_interval) % 12
        
        candidates = [p for p in scale_pitches if p % 12 == target_pc]
        if not candidates:
            return current
        return min(candidates, key=lambda p: abs(p - current))
    
    def _should_octave_jump(self, bar: int, step: int, style: str) -> bool:
        """Determine if an octave jump should occur."""
        probability = 0.08 if style == "rawstyle" else 0.05
        # More likely at phrase boundaries
        if bar % 2 == 0 and step == 0:
            probability *= 2
        return random.random() < probability
    
    def _find_next_hit(self, current_step: int, rhythm_pattern: List[int]) -> int:
        """Find how many steps until next hit (for duration calculation)."""
        pattern_len = len(rhythm_pattern)
        for i in range(1, pattern_len + 1):
            next_idx = (current_step + i) % pattern_len
            if rhythm_pattern[next_idx]:
                return i
        return 4  # Default: quarter note
    
    def _humanize_velocity(
        self, 
        vel_min: int, 
        vel_max: int,
        is_beat1: bool,
        is_strong_bar: bool
    ) -> int:
        """Humanize velocity with musical awareness."""
        base = random.randint(vel_min, vel_max)
        if is_beat1:
            base = min(127, base + 8)  # Accent downbeats
        if is_strong_bar:
            base = min(127, base + 4)
        return base
    
    def _get_stab_positions(self, bar: int, config: GenerationConfig) -> List[float]:
        """
        Get beat positions for chord stabs in rawstyle style.
        Returns start beats for stabs within the bar.
        """
        bar_start = bar * 4.0
        
        if config.style == "rawstyle":
            # Rawstyle: primarily beat 1, sometimes syncopated hits
            positions = [bar_start]
            if random.random() < 0.4:
                positions.append(bar_start + 2.0)  # Beat 3
            if random.random() < 0.25:
                positions.append(bar_start + 2.5)  # Off-beat
        else:
            # Euphoric: every beat or every half bar
            positions = [bar_start, bar_start + 2.0]
        
        return positions
    
    def _build_chord(self, root: int, quality: str, chord_profile: Dict) -> List[int]:
        """
        Build a chord voicing based on quality and profile.
        Returns list of MIDI pitches.
        """
        if quality == "major":
            intervals = [0, 4, 7]
        elif quality == "minor":
            intervals = [0, 3, 7]
        elif quality == "diminished":
            intervals = [0, 3, 6]
        elif quality == "sus2":
            intervals = [0, 2, 7]
        else:
            intervals = [0, 3, 7]  # Default to minor
        
        voicing = chord_profile.get("voicing", "full_triads")
        
        if voicing == "root_fifth":
            intervals = [0, 7]  # Power chord
        
        # Optional: add extensions
        if random.random() < 0.2:
            intervals.append(12)  # Octave
        
        return [root + i for i in intervals if 0 <= root + i <= 127]
