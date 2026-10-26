from typing import List, Optional

from pydantic import BaseModel, Field


class ChordDefinition(BaseModel):
    """Definition of a playable guitar chord."""

    id: str = Field(..., description="Unique chord identifier, e.g. 'c-major'")
    name: str = Field(..., description="Display name, e.g. 'C Major'")
    root: str = Field(..., description="Root note, e.g. 'C'")
    quality: str = Field(..., description="Chord quality, e.g. 'Major' or 'Minor'")
    description: str = Field(..., description="User guidance description")
    finger_count: int = Field(..., ge=1, le=5, description="Associated finger gesture count")
    down_sample: str = Field(..., description="Relative URL to downstroke audio asset")
    up_sample: str = Field(..., description="Relative URL to upstroke audio asset")
    frets: Optional[List[int]] = Field(
        default=None, description="Guitar fret positions (6 strings: E A D G B E)"
    )


DEFAULT_CHORDS: List[ChordDefinition] = [
    ChordDefinition(
        id="c-major",
        name="C Major",
        root="C",
        quality="Major",
        description="One raised finger (Index)",
        finger_count=1,
        down_sample="/assets/audio/chords/c-major-down.wav",
        up_sample="/assets/audio/chords/c-major-up.wav",
        frets=[-1, 3, 2, 0, 1, 0],
    ),
    ChordDefinition(
        id="g-major",
        name="G Major",
        root="G",
        quality="Major",
        description="Two raised fingers (Index + Middle / Peace)",
        finger_count=2,
        down_sample="/assets/audio/chords/g-major-down.wav",
        up_sample="/assets/audio/chords/g-major-up.wav",
        frets=[3, 2, 0, 0, 0, 3],
    ),
    ChordDefinition(
        id="d-major",
        name="D Major",
        root="D",
        quality="Major",
        description="Three raised fingers",
        finger_count=3,
        down_sample="/assets/audio/chords/d-major-down.wav",
        up_sample="/assets/audio/chords/d-major-up.wav",
        frets=[-1, -1, 0, 2, 3, 2],
    ),
    ChordDefinition(
        id="e-minor",
        name="E Minor",
        root="E",
        quality="Minor",
        description="Four raised fingers",
        finger_count=4,
        down_sample="/assets/audio/chords/e-minor-down.wav",
        up_sample="/assets/audio/chords/e-minor-up.wav",
        frets=[0, 2, 2, 0, 0, 0],
    ),
    ChordDefinition(
        id="a-minor",
        name="A Minor",
        root="A",
        quality="Minor",
        description="Five raised fingers (Open palm)",
        finger_count=5,
        down_sample="/assets/audio/chords/a-minor-down.wav",
        up_sample="/assets/audio/chords/a-minor-up.wav",
        frets=[-1, 0, 2, 2, 1, 0],
    ),
]
