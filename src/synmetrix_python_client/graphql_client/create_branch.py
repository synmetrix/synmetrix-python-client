# Generated by ariadne-codegen
# Source: src/synmetrix_python_client/graphql

from typing import Any, Optional

from .base_model import BaseModel


class CreateBranch(BaseModel):
    insert_branches_one: Optional["CreateBranchInsertBranchesOne"]


class CreateBranchInsertBranchesOne(BaseModel):
    id: Any


CreateBranch.model_rebuild()
