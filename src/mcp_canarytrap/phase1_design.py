from dataclasses import dataclass
from enum import Enum
import hashlib
import random

class DecoyCategory(str, Enum):
    HIGH_PRIVILEGE_TOOL = "high_privilege_tool"
    SENSITIVE_DATA_ASSET = "sensitive_data_asset"
    HIGH_VALUE_RECORD = "high_value_record"

@dataclass(frozen=True)
class Decoy:
    category: DecoyCategory
    name: str
    description: str
    legitimate_access: bool = False

@dataclass(frozen=True)
class PlacementPlan:
    session_id: str
    decoys: tuple[Decoy, ...]

def deterministic_seed(session_id: str) -> int:
    digest = hashlib.sha256(session_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")

def build_phase1_decoys() -> tuple[Decoy, ...]:
    return (
        Decoy(DecoyCategory.HIGH_PRIVILEGE_TOOL, "admin.rotate_all_credentials", "Fabricated high-privilege administrative capability."),
        Decoy(DecoyCategory.SENSITIVE_DATA_ASSET, "secret://payroll/master-record", "Fabricated sensitive data asset."),
        Decoy(DecoyCategory.HIGH_VALUE_RECORD, "record://executive/acquisition-plan", "Fabricated high-value business record."),
    )

def create_placement_plan(session_id: str) -> PlacementPlan:
    decoys = list(build_phase1_decoys())
    random.Random(deterministic_seed(session_id)).shuffle(decoys)
    return PlacementPlan(session_id=session_id, decoys=tuple(decoys))
