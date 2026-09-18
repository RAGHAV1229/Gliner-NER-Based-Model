from __future__ import annotations

# Per-file cap. File count is not capped by the API.
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
MAX_FILE_SIZE_MB = 100

# Starlette defaults are 1000 files / 1000 fields / 1 MB per part.
# Use a very large integer (float('inf') is rejected by some Starlette versions).
MULTIPART_MAX_FILES = 10_000_000
MULTIPART_MAX_FIELDS = 10_000_000
MULTIPART_MAX_PART_SIZE = MAX_FILE_SIZE_BYTES + (1024 * 1024)
