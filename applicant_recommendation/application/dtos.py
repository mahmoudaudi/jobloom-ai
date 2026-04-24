from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from matching.payloads import JobPayload, StudentPayload


class RankStudentsRequest(BaseModel):
    job: Optional[JobPayload] = None
    students: Optional[List[StudentPayload]] = None
    useMockData: Optional[bool] = None
