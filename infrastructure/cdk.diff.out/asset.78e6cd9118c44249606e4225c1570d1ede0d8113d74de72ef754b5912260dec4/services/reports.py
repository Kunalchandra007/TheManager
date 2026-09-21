"""S3 report storage with short-lived presigned access URLs."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from docx import Document


class ReportStorageError(RuntimeError):
    pass


class S3ReportService:
    def __init__(self, bucket: str, client: Any = None) -> None:
        if client is None:
            import boto3

            client = boto3.client("s3")
        self._bucket = bucket
        self._client = client

    def create_and_upload(self, markdown: str, session_id: str) -> dict[str, str]:
        document = Document()
        for line in markdown.splitlines():
            document.add_paragraph(line)
        buffer = BytesIO()
        document.save(buffer)
        filename = f"risk-report-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.docx"
        key = f"reports/{session_id}/{filename}"
        try:
            self._client.put_object(Bucket=self._bucket, Key=key, Body=buffer.getvalue(), ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document", ServerSideEncryption="AES256")
            url = self._client.generate_presigned_url("get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=900)
        except Exception as error:
            raise ReportStorageError("Unable to store report in S3") from error
        return {"filename": filename, "s3_key": key, "url": url}
