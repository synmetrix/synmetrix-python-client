# Generated by ariadne-codegen
# Source: src/synmetrix_python_client/graphql

from typing import Optional

from .base_model import BaseModel


class GenDataSchemas(BaseModel):
    gen_dataschemas: Optional["GenDataSchemasGenDataschemas"]


class GenDataSchemasGenDataschemas(BaseModel):
    code: str
    message: Optional[str]


GenDataSchemas.model_rebuild()
