from pydantic import BaseModel, Field
from typing import Optional, List

"""
Pydantic models define the shape of data in requests/responses.
They provide automatic validation and documentation.
"""

class SongBase(BaseModel):
    """Base schema for song data."""
    title: str = Field(..., description="Song title", example="Bohemian Rhapsody")
    artist: str = Field(..., description="Artist name", example="Queen")
    album: Optional[str] = Field(None, description="Album name", example="A Night at the Opera")
    duration: Optional[float] = Field(None, description="Duration in seconds", example=354.0)

class SongCreate(SongBase):
    """Schema for creating a new song."""
    pass

class SongResponse(SongBase):
    """Schema for song in API responses."""
    id: int = Field(..., description="Unique song ID")
    title: str = Field(..., description="Song title")
    artist: str = Field(..., description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    
    class Config:
        # Allows creating from ORM models (SQLAlchemy)
        from_attributes = True

class SongListResponse(BaseModel):
    """Schema for list of songs."""
    songs: List[SongResponse]
    total: int

class MatchResult(BaseModel):
    """Schema for song match results."""
    matched: bool = Field(..., description="Whether a match was found")
    song: Optional[SongResponse] = Field(None, description="Matched song details")
    confidence: Optional[int] = Field(None, description="Number of matching fingerprints")
    confidence_percentage: Optional[float] = Field(None, description="Match confidence as percentage")
    
class UploadResponse(BaseModel):
    """Schema for file upload response."""
    message: str
    song_id: int
    fingerprints_generated: int

class DatabaseStats(BaseModel):
    """Schema for database statistics."""
    total_songs: int
    total_fingerprints: int
    avg_fingerprints_per_song: float

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None