import sys, requests
sys.stdout.reconfigure(encoding="utf-8")

base = "http://localhost:8000"

# 1. Discover
r1 = requests.get(f"{base}/discover?domain=finance")
uc_count = len(r1.json()["use_cases"])
print(f"[1] discover: {uc_count} use cases for finance")

# 2. Finalize
r2 = requests.post(f"{base}/finalize", json={"domain": "finance", "use_case_id": 1})
fin = r2.json()
print(f"[2] finalize HTTP status: {r2.status_code}")
print(f"    response keys: {list(fin.keys())}")
print(f"    confirmation: {fin['confirmation_message'][:70]}")

crt = fin.get("copy_ready_text", "")
cp  = fin.get("claude_prompt", "")
print(f"    copy_ready_text: {len(crt)} chars")
print(f"    claude_prompt:   {len(cp)} chars")

# Spot-check copy_ready content
checks = {
    "Title":             "Title:" in crt,
    "Architecture/Flow": "Architecture" in crt,
    "ROI Estimate":      "ROI Estimate" in crt,
    "Readiness Scores":  "Readiness Scores" in crt,
    "Action Plan":       "Action Plan" in crt,
}
print("\n    Copy-ready content checks:")
for label, ok in checks.items():
    print(f"      {label}: {'PASS' if ok else 'FAIL'}")

# Spot-check claude prompt
print(f"\n    Claude prompt has 13 sections: {'13.' in cp}")
print(f"    Claude prompt mentions domain: {'finance' in cp.lower() or 'Finance' in cp}")

passed = r2.status_code == 200 and crt and cp and all(checks.values())
print(f"\n{'Phase 4 ALL PASSED' if passed else 'Phase 4 SOME CHECKS FAILED'}")
