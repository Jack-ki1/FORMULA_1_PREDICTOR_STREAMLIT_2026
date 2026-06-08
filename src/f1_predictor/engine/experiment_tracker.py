"""
Lightweight experiment tracking that writes JSON logs.

Designed to be replaced with MLflow or W&B when the project scales,
but provides experiment lineage without external dependencies.
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


EXPERIMENTS_DIR = Path("experiments")


class ExperimentTracker:
    """
    Lightweight experiment tracking that writes JSON logs.
    
    Designed to be replaced with MLflow or W&B when the project scales,
    but provides experiment lineage without external dependencies.
    """
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.run_id = self._generate_run_id()
        self.run_dir = EXPERIMENTS_DIR / experiment_name / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._metadata = {
            "run_id": self.run_id,
            "experiment": experiment_name,
            "started_at": datetime.utcnow().isoformat(),
            "params": {},
            "metrics": {},
            "tags": {},
        }

    def _generate_run_id(self) -> str:
        ts = datetime.utcnow().isoformat()
        return hashlib.md5(ts.encode()).hexdigest()[:8]

    def log_param(self, key: str, value: Any) -> None:
        self._metadata["params"][key] = value

    def log_params(self, params: Dict[str, Any]) -> None:
        self._metadata["params"].update(params)

    def log_metric(self, key: str, value: float, step: int = None) -> None:
        if key not in self._metadata["metrics"]:
            self._metadata["metrics"][key] = []
        entry = {"value": value, "timestamp": datetime.utcnow().isoformat()}
        if step is not None:
            entry["step"] = step
        self._metadata["metrics"][key].append(entry)

    def log_artifact(self, filename: str, content: Any) -> None:
        artifact_path = self.run_dir / filename
        with open(artifact_path, "w") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                json.dump(content, f, indent=2)

    def end_run(self) -> None:
        self._metadata["ended_at"] = datetime.utcnow().isoformat()
        with open(self.run_dir / "metadata.json", "w") as f:
            json.dump(self._metadata, f, indent=2)
