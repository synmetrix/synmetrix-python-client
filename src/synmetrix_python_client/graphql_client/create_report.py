# Generated by ariadne-codegen
# Source: src/synmetrix_python_client/graphql

from typing import Any, Optional

from .base_model import BaseModel


class CreateReport(BaseModel):
    insert_reports_one: Optional["CreateReportInsertReportsOne"]


class CreateReportInsertReportsOne(BaseModel):
    id: Any


CreateReport.model_rebuild()
