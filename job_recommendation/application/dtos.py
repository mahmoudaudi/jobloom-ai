from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from matching.payloads import JobPayload, StudentPayload


class RankJobsRequest(BaseModel):
    student: Optional[StudentPayload] = None
    jobs: Optional[List[JobPayload]] = None
    useMockData: Optional[bool] = None
