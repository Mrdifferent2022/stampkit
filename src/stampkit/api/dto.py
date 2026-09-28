"""Request/response DTOs for the API layer.

The part input is abstracted over local paths and cloud object references so
the same API works on a desktop and behind a remote bridge.
"""

from __future__ import annotations

import enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from stampkit.model.context import KernelSettings


class PartInputKind(enum.StrEnum):
    LOCAL_PATH = "local_path"
    BASE64_CONTENT = "base64_content"
    OBJECT_REF = "object_ref"
    ACTIVE_DOCUMENT = "active_document"


class LocalPathInput(BaseModel):
    kind: Literal[PartInputKind.LOCAL_PATH] = PartInputKind.LOCAL_PATH
    path: str


class Base64ContentInput(BaseModel):
    kind: Literal[PartInputKind.BASE64_CONTENT] = PartInputKind.BASE64_CONTENT
    filename: str
    content_base64: str


class ObjectRefInput(BaseModel):
    """Reference to an object in remote object storage (cloud deployments)."""

    kind: Literal[PartInputKind.OBJECT_REF] = PartInputKind.OBJECT_REF
    bucket: str
    key: str


class ActiveDocumentInput(BaseModel):
    """Evaluate the currently open document inside a live CAD session."""

    kind: Literal[PartInputKind.ACTIVE_DOCUMENT] = PartInputKind.ACTIVE_DOCUMENT
    document_name: str = ""


PartInput = Annotated[
    LocalPathInput | Base64ContentInput | ObjectRefInput | ActiveDocumentInput,
    Field(discriminator="kind"),
]


class EvaluateRequest(BaseModel):
    part: PartInput
    thickness_mm: float = Field(gt=0)
    material: str
    ruleset: str = "default"
    kernel_settings: KernelSettings = Field(default_factory=KernelSettings)
