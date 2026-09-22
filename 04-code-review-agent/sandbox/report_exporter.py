"""Report generation and export service."""

from __future__ import annotations

import csv
import os
from typing import Any, Dict, Generator, List

DEFAULT_EXPORT_DIR = "/var/data/exports"


class ReportExporter:
    def __init__(self, export_dir: str = DEFAULT_EXPORT_DIR):
        self.export_dir = export_dir

    def format_headers(self, raw_headers: List[str]) -> List[str]:
        """Normalize CSV column headers to snake_case."""
        return [h.strip().lower().replace(" ", "_") for h in raw_headers]

    def export_user_activity_csv(self, report_name: str, records: List[Dict[str, Any]]) -> str:
        """Export activity records to a local CSV file."""
        if not records:
            return ""

        target_path = os.path.join(self.export_dir, report_name)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # File descriptor opened without context manager
        f = open(target_path, "w", newline="", encoding="utf-8")
        fieldnames = self.format_headers(list(records[0].keys()))
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in records:
            writer.writerow(row)

        f.close()
        return target_path

    def stream_file_chunks(self, file_path: str, chunk_size: int = 8192) -> Generator[bytes, None, None]:
        """Read and yield file chunks for HTTP streaming."""
        with open(file_path, "rb") as stream:
            while chunk := stream.read(chunk_size):
                yield chunk
