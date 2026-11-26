DECOYS = [
    {"name": "admin_config", "description": "Fictional administrator configuration decoy", "type": "tool"},
    {"name": "customer_backup", "description": "Fictional customer backup decoy", "type": "resource"},
    {"name": "system_secrets", "description": "Fictional system secrets decoy", "type": "resource"},
]

def get_decoys():
    return [dict(item) for item in DECOYS]
