from pydantic import BaseModel
from typing import Optional
from enum import Enum


class VoiceChoice(str, Enum):
    # Male
    sumit = "sumit"
    rahul = "rahul"
    ashutosh = "ashutosh"
    shubh = "shubh"
    aditya = "aditya"
    sunny = "sunny"
    # Female
    priya = "priya"
    pooja = "pooja"
    simran = "simran"
    ishita = "ishita"
    shreya = "shreya"
    kavitha = "kavitha"


class LanguageChoice(str, Enum):
    en = "en"
    hi = "hi"


class GeneratePPTRequest(BaseModel):
    voice: VoiceChoice = VoiceChoice.sumit
    language: LanguageChoice = LanguageChoice.en


class GenerateBothRequest(BaseModel):
    voice: VoiceChoice = VoiceChoice.sumit


class VoiceInfo(BaseModel):
    id: str
    gender: str
    style: str
    preview_en: str
    preview_hi: str


class VoicesResponse(BaseModel):
    voices: list[VoiceInfo]
    languages: dict[str, str]