# Generated by ariadne-codegen
# Source: src/synmetrix_python_client/graphql

from typing import Any, Optional

from .base_model import BaseModel


class DeleteCredentials(BaseModel):
    delete_sql_credentials_by_pk: Optional["DeleteCredentialsDeleteSqlCredentialsByPk"]


class DeleteCredentialsDeleteSqlCredentialsByPk(BaseModel):
    id: Any


DeleteCredentials.model_rebuild()
