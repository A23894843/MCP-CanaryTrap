DECOYS = [
    {"name": "admin_config", "description": "Fictional administrator configuration decoy.", "severity": "HIGH"},
    {"name": "customer_backup", "description": "Fictional customer backup decoy.", "severity": "CRITICAL"},
    {"name": "system_secrets", "description": "Fictional system secrets decoy.", "severity": "CRITICAL"},
]
def get_decoys():
    return [item.copy() for item in DECOYS]
def get_decoy(name):
    return next((item.copy() for item in DECOYS if item["name"] == name), None)
