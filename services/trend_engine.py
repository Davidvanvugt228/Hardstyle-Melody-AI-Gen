"""
Trend Engine
Manages hardstyle/rawstyle trend data, pattern selection, and analytics.
Implements weighted probability system based on frequency + recency.
"""

import json
import os
import random
import math
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime


TREND_DATA_DIR = Path(__file__).parent.parent / "trend-data"
ANALYTICS_DIR = Path(__file__).parent.parent / "analytics"


class TrendEngine:
    """
    Manages trend data and pattern selection with weighted probabilities.
    Implements a non-destructive learning loop.
    """
    
    def __init__(self):
        self.melody_patterns = self._load_json("melody_patterns.json")
        self.chord_progressions = self._load_json("chord_progressions.json")
        self.rhythm_profiles = self._load_json("rhythm_profiles.json")
        self.genre_profiles = self._load_json("genre_profiles.json")
        self._usage_cache: Dict[str, int] = {}
        self._load_analytics()
    
    def _load_json(self, filename: str) -> Dict:
        path = TREND_DATA_DIR / filename
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}
    
    def _load_analytics(self):
        """Load usage analytics to inform weighted selection."""
        analytics_path = ANALYTICS_DIR / "usage_data.json"
        if analytics_path.exists():
            with open(analytics_path, "r") as f:
                data = json.load(f)
                self._usage_cache = data.get("pattern_downloads", {})
    
    def select_melody_pattern(
        self, 
        style: str = "rawstyle",
        energy: Optional[str] = None,
        avoid_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Select a melody pattern using weighted probability.
        Weight = base_weight * recency_score * (1 + analytics_boost)
        """
        patterns = self.melody_patterns.get("patterns", [])
        avoid_ids = avoid_ids or []
        
        candidates = [
            p for p in patterns 
            if p["id"] not in avoid_ids and
            (p.get("style") == style or style == "any")
        ]
        
        if energy:
            energy_filtered = [p for p in candidates if p.get("energy") == energy]
            if energy_filtered:
                candidates = energy_filtered
        
        if not candidates:
            candidates = patterns  # Fallback to all patterns
        
        weights = self._compute_weights(candidates)
        selected = random.choices(candidates, weights=weights, k=1)[0]
        return selected
    
    def select_chord_progression(self, style: str = "rawstyle") -> Dict:
        """Select chord progression with style-aware weighting."""
        progressions = self.chord_progressions.get("progressions", [])
        
        candidates = [
            p for p in progressions
            if p.get("style") == style or p.get("style") == "both"
        ]
        
        if not candidates:
            candidates = progressions
        
        weights = self._compute_weights(candidates)
        return random.choices(candidates, weights=weights, k=1)[0]
    
    def get_genre_profile(self, style: str = "rawstyle") -> Dict:
        """Return the genre profile for style configuration."""
        profiles = self.genre_profiles.get("profiles", {})
        return profiles.get(style, profiles.get("rawstyle", {}))
    
    def _compute_weights(self, patterns: List[Dict]) -> List[float]:
        """
        Compute selection weights for patterns.
        Formula: base_weight * recency_score * analytics_boost
        """
        weights = []
        for p in patterns:
            base = p.get("weight", 0.5)
            recency = p.get("recency_score", 0.5)
            
            # Analytics boost: more downloads = small boost (max 1.5x)
            downloads = self._usage_cache.get(p["id"], 0)
            analytics_boost = 1.0 + min(downloads * 0.05, 0.5)
            
            weight = base * recency * analytics_boost
            weights.append(max(weight, 0.01))
        
        return weights
    
    def detect_style_from_bpm(self, bpm: float) -> str:
        """Detect likely style from BPM."""
        if bpm < 155:
            return "rawstyle"
        elif bpm > 165:
            return "euphoric"
        else:
            # Mixed zone - slightly bias toward rawstyle (more popular currently)
            return random.choices(["rawstyle", "euphoric"], weights=[0.6, 0.4])[0]
    
    def record_download(self, pattern_ids: List[str]):
        """
        Record pattern downloads for analytics.
        Non-destructive: only increases weights, bounded by cap.
        """
        ANALYTICS_DIR.mkdir(exist_ok=True)
        analytics_path = ANALYTICS_DIR / "usage_data.json"
        
        if analytics_path.exists():
            with open(analytics_path, "r") as f:
                data = json.load(f)
        else:
            data = {"pattern_downloads": {}, "sessions": []}
        
        for pid in pattern_ids:
            current = data["pattern_downloads"].get(pid, 0)
            data["pattern_downloads"][pid] = min(current + 1, 100)  # Cap at 100
        
        data["sessions"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "patterns": pattern_ids
        })
        
        # Keep only last 1000 sessions
        data["sessions"] = data["sessions"][-1000:]
        
        with open(analytics_path, "w") as f:
            json.dump(data, f, indent=2)
        
        # Refresh cache
        self._usage_cache = data["pattern_downloads"]
    
    def get_trend_summary(self) -> Dict:
        """Return a summary of current trend data for the /trends endpoint."""
        patterns = self.melody_patterns.get("patterns", [])
        progressions = self.chord_progressions.get("progressions", [])
        
        # Top patterns by composite score
        scored = sorted(
            patterns,
            key=lambda p: p.get("weight", 0) * p.get("recency_score", 0),
            reverse=True
        )
        
        return {
            "version": self.melody_patterns.get("version", "1.0.0"),
            "last_updated": self.melody_patterns.get("last_updated"),
            "bpm_range": self.melody_patterns.get("bpm_range", {}),
            "top_patterns": [
                {
                    "id": p["id"],
                    "style": p["style"],
                    "energy": p.get("energy"),
                    "composite_score": round(p.get("weight", 0) * p.get("recency_score", 0), 3)
                }
                for p in scored[:5]
            ],
            "available_styles": list(set(p["style"] for p in patterns)),
            "chord_progressions_count": len(progressions),
            "analytics": {
                "total_tracked_patterns": len(self._usage_cache),
                "top_downloaded": max(self._usage_cache, key=self._usage_cache.get) 
                    if self._usage_cache else None
            }
        }


# Singleton instance
_trend_engine: Optional[TrendEngine] = None


def get_trend_engine() -> TrendEngine:
    global _trend_engine
    if _trend_engine is None:
        _trend_engine = TrendEngine()
    return _trend_engine
