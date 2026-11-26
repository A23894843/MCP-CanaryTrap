"""Command-line entry point for local MCP dependency/config auditing."""
import argparse
import json
from pathlib import Path
from app.security.vulnerability_auditor import audit_paths

def main():
    parser = argparse.ArgumentParser(description="MCP-CanaryTrap local security auditor")
    parser.add_argument("paths", nargs="*", default=["."], help="Files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()
    findings = audit_paths(args.paths or ["."])
    report = {
        "case_study": "CVE-2025-6514",
        "affected_range": "mcp-remote >=0.0.5 and <=0.1.15",
        "fixed_version": "0.1.16",
        "findings_count": len(findings),
        "findings": findings,
        "note": "A config reference does not prove the resolved version. Verify lockfiles, npm cache and runtime package resolution.",
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("MCP-CanaryTrap | Local Security Audit")
        print("Case study: CVE-2025-6514")
        print("Affected mcp-remote versions: 0.0.5 through 0.1.15; fixed: 0.1.16")
        print("-" * 68)
        if not findings:
            print("No matching dependency/config references found in the selected paths.")
        for item in findings:
            print(f"[{item['risk']}] {item['type']} | {item['file']}")
            print(f"  Version/reference: {item['version_spec']} | {item['detail']}")
        print("-" * 68)
        print(report["note"])

if __name__ == "__main__":
    main()
