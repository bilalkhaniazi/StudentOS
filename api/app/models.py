from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CourseEntry(BaseModel):
    subject: str
    courseNumber: str
    code: str
    level: str | None = None
    title: str | None = None
    creditHours: float | None = None
    gradeLetter: str | None = None
    repeatFlag: str | None = None
    term: str | None = None
    termSource: Literal["Period", "Term"] | None = None
    status: Literal["completed", "in_progress", "planned"] = "completed"


class SkillEntry(BaseModel):
    label: str
    evidence: Literal["coursework", "project", "certification", "self_report"] = "self_report"


class ProjectEntry(BaseModel):
    name: str
    summary: str | None = None
    technologies: list[str] = Field(default_factory=list)
    demonstratesSkills: list[str] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    name: str
    taggedSkills: list[str] = Field(default_factory=list)


class CurriculumBlock(BaseModel):
    kind: Literal["degree", "postBaccalaureateBadge", "other"] = "degree"
    status: Literal["sought", "awarded"] = "sought"
    college: str | None = None
    major: str | None = None
    degreeDateOptional: str | None = None


class StudentProfile(BaseModel):
    syntheticId: str
    displayName: str
    institution: str = "GVSU"
    transcriptLevel: Literal["Undergraduate", "Masters"] = "Undergraduate"
    transcriptType: str = "Advising"
    college: str | None = "College of Computing"
    degreeLine: str | None = None
    major: str | None = None
    majorAndDepartment: str | None = None
    catalogYear: str | None = "2026-2027"
    targetCareer: str | None = None
    careerInterests: list[str] = Field(default_factory=list)
    remainingCredits: float | None = None
    termCreditPreference: str = "softCap15"
    summary: str | None = None
    skills: list[SkillEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    curriculum: list[CurriculumBlock] = Field(default_factory=list)
    courses: list[CourseEntry] = Field(default_factory=list)
    editable: bool = True
    synthetic: bool = False


class ProfileUpdate(BaseModel):
    displayName: str | None = None
    transcriptLevel: Literal["Undergraduate", "Masters"] | None = None
    college: str | None = None
    degreeLine: str | None = None
    major: str | None = None
    majorAndDepartment: str | None = None
    catalogYear: str | None = None
    targetCareer: str | None = None
    careerInterests: list[str] | None = None
    remainingCredits: float | None = None
    summary: str | None = None
    skills: list[SkillEntry] | None = None
    projects: list[ProjectEntry] | None = None
    certifications: list[CertificationEntry] | None = None
    curriculum: list[CurriculumBlock] | None = None
    courses: list[CourseEntry] | None = None


class SessionUpdate(BaseModel):
    activeProfileId: str


class CareerPick(BaseModel):
    targetCareer: str


class TranscriptImportResult(BaseModel):
    accepted: bool
    filename: str | None = None
    message: str
    parsed: bool = False
    mappedCourses: list[dict[str, Any]] = Field(default_factory=list)
