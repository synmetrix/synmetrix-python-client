# Generated by ariadne-codegen
# Source: src/synmetrix_python_client/graphql

from typing import Any, Optional

from .base_model import BaseModel


class CreateVersion(BaseModel):
    insert_versions_one: Optional["CreateVersionInsertVersionsOne"]


class CreateVersionInsertVersionsOne(BaseModel):
    id: Any


CreateVersion.model_rebuild()
