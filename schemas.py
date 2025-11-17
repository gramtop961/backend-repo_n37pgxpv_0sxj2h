"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- RequestItem -> "requestitem" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="BCrypt hashed password")
    photo_url: Optional[str] = Field(None, description="Avatar URL")

class Location(BaseModel):
    lat: float
    lng: float

class RequestItem(BaseModel):
    """
    Requests sent by users (messages, media, contact, location)
    Collection name: "requestitem"
    """
    user_id: str = Field(..., description="Sender user id (as string)")
    type: str = Field(..., description="One of: text, voice, photo, contact, location")
    text: Optional[str] = None
    voice_url: Optional[str] = None
    photo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    location: Optional[Location] = None
    status: str = Field("sent", description="Request status")
    meta: Optional[Dict[str, Any]] = None
