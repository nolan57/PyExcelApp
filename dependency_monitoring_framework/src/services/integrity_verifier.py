from ..interfaces.health_check_plugin import HealthCheckPlugin
from ..core.event_bus import EventBus
import hashlib
import os
from typing import Dict
from ..config import settings

class IntegrityVerifier(HealthCheckPlugin):
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.checksum_file = settings.get('integrity_verifier.checksum_file')
        self.last_error = None

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def check(self) -> Dict:
        """Verify file integrity using checksums"""
        results = {}
        try:
            if not os.path.exists(self.checksum_file):
                raise FileNotFoundError(f"Checksum file not found: {self.checksum_file}")

            with open(self.checksum_file) as f:
                for line in f:
                    expected_checksum, file_path = line.strip().split()
                    if not os.path.exists(file_path):
                        results[file_path] = 'File not found'
                        continue

                    actual_checksum = self._calculate_checksum(file_path)
                    results[file_path] = 'OK' if actual_checksum == expected_checksum else 'Checksum mismatch'

            return results
        except Exception as e:
            self.last_error = str(e)
            self.event_bus.publish('integrity_check_failed', {'error': str(e)})
            raise

    def get_status(self) -> Dict:
        return {
            'checksum_file': self.checksum_file,
            'last_error': self.last_error
        }

    def configure(self, config: Dict):
        if 'checksum_file' in config:
            self.checksum_file = config['checksum_file']
