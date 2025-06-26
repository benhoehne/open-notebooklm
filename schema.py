"""
schema.py - Pydantic models for structured podcast generation
"""

from typing import List
from pydantic import BaseModel, Field


class DialogueItem(BaseModel):
    """A single dialogue item with speaker and text."""
    
    speaker: str = Field(
        ..., 
        description="The speaker name, should be either the host name or guest name"
    )
    text: str = Field(
        ..., 
        description="The dialogue text - must not be empty"
    )


class ShortDialogue(BaseModel):
    """The dialogue between the host and guest for short-form content."""

    scratchpad: str = Field(
        ..., 
        description="Your thinking process and planning for the dialogue"
    )
    name_of_guest: str = Field(
        ..., 
        description="The name of the guest speaker"
    )
    dialogue: List[DialogueItem] = Field(
        ..., 
        description="A list of dialogue items, typically between 11 to 17 items"
    )


class MediumDialogue(BaseModel):
    """The dialogue between the host and guest for medium-form content."""

    scratchpad: str = Field(
        ..., 
        description="Your thinking process and planning for the dialogue"
    )
    name_of_guest: str = Field(
        ..., 
        description="The name of the guest speaker"
    )
    dialogue: List[DialogueItem] = Field(
        ..., 
        description="A list of dialogue items, typically between 19 to 29 items"
    )


class LongDialogue(BaseModel):
    """The dialogue between the host and guest for long-form content."""

    scratchpad: str = Field(
        ..., 
        description="Your thinking process and planning for the dialogue"
    )
    name_of_guest: str = Field(
        ..., 
        description="The name of the guest speaker"
    )
    dialogue: List[DialogueItem] = Field(
        ..., 
        description="A list of dialogue items, typically between 70 to 100 items for comprehensive coverage"
    )


# Schema selection function
def get_dialogue_schema(length: str):
    """Get the appropriate dialogue schema based on length."""
    schemas = {
        "short": ShortDialogue,
        "medium": MediumDialogue,
        "long": LongDialogue
    }
    return schemas.get(length, MediumDialogue)
