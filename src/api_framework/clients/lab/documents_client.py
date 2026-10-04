from uuid import UUID

from api_framework.core.api_client import ApiClient


class DocumentsClient:
    def __init__(self, api: ApiClient, session=None):
        self.api, self.session = api, session

    def headers(self):
        return self.session.headers() if self.session else {}

    def upload(self, filename: str, content: bytes, key: str, content_type="text/plain"):
        return self.api.request(
            "POST",
            "/documents",
            headers={
                **self.headers(),
                "Idempotency-Key": key,
            },
            multipart={"file": {"name": filename, "mimeType": content_type, "buffer": content}},
        )

    def metadata(self, document_id: str):
        return self.api.request("GET", f"/documents/{UUID(document_id)}", headers=self.headers())

    def download(self, document_id: str):
        return self.api.request(
            "GET", f"/documents/{UUID(document_id)}/download", headers=self.headers()
        )

    def delete(self, document_id: str):
        return self.api.request("DELETE", f"/documents/{UUID(document_id)}", headers=self.headers())
