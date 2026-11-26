# Manual Verification Checklist

Fill in actual results during your run.

| Check | Expected result | Actual result |
|---|---|---|
| FastAPI startup | Startup complete | |
| Dashboard | API connected | |
| MCP client | Lists four tools | |
| `weather_search` | No decoy event | |
| `admin_config` | HIGH DECOY_ACCESS event, source mcp | |
| `customer_backup` | CRITICAL DECOY_ACCESS event, source mcp | |
| `system_secrets` | CRITICAL DECOY_ACCESS event, source mcp | |
| HTTP manual inspection | Detects configured decoy | |
| SQLite query | Event records visible | |

SQL:
```sql
SELECT id,target_name,event_type,severity,source,timestamp
FROM security_events ORDER BY id DESC;
```
