from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ReleaseCase(Model):
    case_id: str = Field(min_length=1)
    selection: Literal["candidate", "approve"]
    requires_video_rerecording: bool = False


class ReleaseTask(Model):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    title: str = Field(min_length=1)
    base_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    merge_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    cases: list[ReleaseCase] = Field(default_factory=list)

    @field_validator("cases")
    @classmethod
    def unique_cases(cls, cases: list[ReleaseCase]) -> list[ReleaseCase]:
        if len({case.case_id for case in cases}) != len(cases):
            raise ValueError("release task contains duplicate case IDs")
        return cases

    @field_validator("id")
    @classmethod
    def safe_id(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or value in {".", ".."} or len(path.parts) != 1:
            raise ValueError("task id must be one safe directory name")
        return value


class ReleaseManifest(Model):
    schema_version: Literal["ibench-release/v1"]
    name: str = Field(min_length=1)
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    instruction_profiles: list[Literal["intent", "intent-actions"]] = Field(min_length=1)
    default_instruction_profile: Literal["intent", "intent-actions"]
    tasks: list[ReleaseTask] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_members(self) -> ReleaseManifest:
        profiles = self.instruction_profiles
        if len(profiles) != len(set(profiles)):
            raise ValueError("instruction profiles must be unique")
        if self.default_instruction_profile not in profiles:
            raise ValueError("default instruction profile is not declared")
        for field in ("id", "name"):
            values = [getattr(task, field) for task in self.tasks]
            if len(values) != len(set(values)):
                raise ValueError(f"task {field} values must be unique")
        return self


class UserTask(Model):
    intent: str = Field(min_length=1)
    actions: list[str] = Field(min_length=1)

    @field_validator("actions")
    @classmethod
    def meaningful_actions(cls, actions: list[str]) -> list[str]:
        if any(not action.strip() for action in actions):
            raise ValueError("actions must not contain blank entries")
        return actions


class TheoryReference(Model):
    title: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class VideoStep(Model):
    kind: Literal["step"]
    t: float = Field(ge=0, allow_inf_nan=False, strict=True)
    label: str = Field(min_length=1)


class VideoClaim(Model):
    kind: Literal["check", "flag"]
    t: float = Field(ge=0, allow_inf_nan=False, strict=True)
    note: str = Field(min_length=1)


VideoChapter = Annotated[VideoStep | VideoClaim, Field(discriminator="kind")]


class VideoGuide(Model):
    summary: str = Field(min_length=1)
    chapters: list[VideoChapter] = Field(default_factory=list)


class CaseDefinition(Model):
    issue_id: str = Field(min_length=1)
    given: str = Field(min_length=1)
    when: str = Field(min_length=1)
    observed: str = Field(min_length=1)
    require: str = Field(min_length=1)
    allow: list[str] = Field(default_factory=list)
    theory: list[TheoryReference] = Field(min_length=1)


class CaseRubric(Model):
    schema_version: Literal["case-rubric/v1"]
    case_id: str = Field(min_length=1)
    definition: CaseDefinition
    reference_observation: str = Field(min_length=1)
    requirement_rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def identity_matches_definition(self) -> CaseRubric:
        if self.case_id != self.definition.issue_id:
            raise ValueError("rubric and definition identities do not match")
        return self


class Case(Model):
    case_id: str = Field(min_length=1)
    input: str = Field(min_length=1)
    replay_root: str = Field(min_length=1)
    verdict_template: str = Field(min_length=1)
    capture: str = Field(min_length=1)


class CaseManifest(Model):
    schema_version: Literal["ibench-score-manifest/v1"]
    task_id: str = Field(min_length=1)
    validate_path: str = Field(alias="validate", min_length=1)
    cases: list[Case] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_cases(self) -> CaseManifest:
        for field in ("case_id", "input"):
            values = [getattr(case, field) for case in self.cases]
            if len(values) != len(set(values)):
                raise ValueError(f"case {field} values must be unique")
        return self
