"""
schema.py
"""

from typing import Literal, List, Union

from pydantic import BaseModel, Field


class DialogueItem(BaseModel):
    """A single dialogue item."""

    speaker: Literal["Host (Sam)", "Guest"]
    text: str


class ShortDialogue(BaseModel):
    """The dialogue between the host and guest."""

    scratchpad: str
    name_of_guest: str
    dialogue: List[DialogueItem] = Field(
        ..., description="A list of dialogue items, typically between 11 to 17 items"
    )


class MediumDialogue(BaseModel):
    """The dialogue between the host and guest."""

    scratchpad: str
    name_of_guest: str
    dialogue: List[DialogueItem] = Field(
        ..., description="A list of dialogue items, typically between 19 to 29 items"
    )


class LongDialogue(BaseModel):
    """The dialogue between the host and guest for long-form content."""

    scratchpad: str
    name_of_guest: str
    dialogue: List[DialogueItem] = Field(
        ..., description="A list of dialogue items, typically between 70 to 100 items for comprehensive coverage"
    )


# Dynamic schema creation functions for custom host names
def create_dynamic_dialogue_item(host_name: str = "Sam"):
    """Create a DialogueItem class with custom host name."""
    
    class DynamicDialogueItem(BaseModel):
        """A single dialogue item with custom speaker names."""
        speaker: Literal[f"Host ({host_name})", "Guest"]
        text: str
    
    return DynamicDialogueItem


def create_short_dialogue_schema(host_name: str = "Sam"):
    """Create a ShortDialogue schema with custom host name."""
    
    DialogueItemClass = create_dynamic_dialogue_item(host_name)
    
    class DynamicShortDialogue(BaseModel):
        """The dialogue between the host and guest."""
        scratchpad: str
        name_of_guest: str
        dialogue: List[DialogueItemClass] = Field(
            ..., description="A list of dialogue items, typically between 11 to 17 items"
        )
    
    return DynamicShortDialogue


def create_medium_dialogue_schema(host_name: str = "Sam"):
    """Create a MediumDialogue schema with custom host name."""
    
    DialogueItemClass = create_dynamic_dialogue_item(host_name)
    
    class DynamicMediumDialogue(BaseModel):
        """The dialogue between the host and guest."""
        scratchpad: str
        name_of_guest: str
        dialogue: List[DialogueItemClass] = Field(
            ..., description="A list of dialogue items, typically between 19 to 29 items"
        )
    
    return DynamicMediumDialogue


def create_long_dialogue_schema(host_name: str = "Sam"):
    """Create a LongDialogue schema with custom host name."""
    
    DialogueItemClass = create_dynamic_dialogue_item(host_name)
    
    class DynamicLongDialogue(BaseModel):
        """The dialogue between the host and guest for long-form content."""
        scratchpad: str
        name_of_guest: str
        dialogue: List[DialogueItemClass] = Field(
            ..., description="A list of dialogue items, typically between 70 to 100 items for comprehensive coverage"
        )
    
    return DynamicLongDialogue
