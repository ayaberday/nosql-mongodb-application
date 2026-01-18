from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class StudentCreate(BaseModel):
    firstName: str = Field(min_length=2)
    lastName: str = Field(min_length=2)
    email: EmailStr
    program: str
    school: str = "EMSI"
    timezone: str = "Africa/Casablanca"

class StudentOut(BaseModel):
    id: str
    firstName: str
    lastName: str
    email: str
    program: str
    school: str
    timezone: str

from pydantic import BaseModel, Field
from typing import Optional, List

class SubjectCreate(BaseModel):
    name: str = Field(min_length=2)
    program: str = Field(min_length=2)
    coefficient: Optional[int] = Field(default=2, ge=1, le=10)
    color: Optional[str] = None

class SubjectOut(BaseModel):
    id: str
    name: str
    program: str
    coefficient: Optional[int] = None
    color: Optional[str] = None

from datetime import datetime
from typing import List, Optional, Literal

Mood = Literal["Motivé", "Neutre", "Fatigué", "Stressé", "Content"]
Period = Literal["matin", "apres_midi", "soir", "nuit"]
SessionType = Literal["cours", "exercices", "resume", "quiz"]

class SessionCreate(BaseModel):
    studentId: str
    subjectId: str
    startedAt: datetime
    durationMin: int = Field(ge=1, le=600)
    difficulty: int = Field(ge=1, le=5)
    mood: Mood
    period: Period
    type: SessionType
    tags: Optional[List[str]] = []
    notes: Optional[str] = None

class SessionOut(BaseModel):
    id: str
    studentId: str
    subjectId: str
    startedAt: datetime
    durationMin: int
    difficulty: int
    mood: str
    period: str
    type: str
    tags: List[str]
    notes: Optional[str]
