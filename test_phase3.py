import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

base = "http://localhost:8000"

# Test 1: Known domain - finance
r1 = requests.get(f"{base}/discover?domain=finance")
ucs = r1.json()["use_cases"]
has_arch = "architecture_diagram" in ucs[0]
print(f"[TEST 1] finance: {len(ucs)} use cases | has_architecture_diagram={has_arch}")
print(f"         first title: {ucs[0]['title']}")
print(f"         arch: {ucs[0].get('architecture_diagram', 'MISSING')[:80]}")
print()

# Test 2: Niche compound domain
r2 = requests.get(f"{base}/discover?domain=supply chain for shipping industries")
ucs2 = r2.json()["use_cases"]
print(f"[TEST 2] niche domain: {len(ucs2)} use cases")
print(f"         first title: {ucs2[0]['title']}")
has_arch2 = "architecture_diagram" in ucs2[0]
print(f"         has_architecture_diagram={has_arch2}")
print()

# Test 3: Another wild domain
r3 = requests.get(f"{base}/discover?domain=AI for small coffee shops")
ucs3 = r3.json()["use_cases"]
print(f"[TEST 3] coffee shops: {len(ucs3)} use cases")
print(f"         first title: {ucs3[0]['title']}")
print()

# Test 4: Case study
r4 = requests.post(f"{base}/case-study", json={"domain": "finance", "use_case_id": 1})
cs = r4.json()
uc_title = cs["use_case"]["title"]
kpi_count = len(cs["success_metrics"])
steps_count = len(cs["timeline_estimate"])
print(f"[TEST 4] case-study: title={uc_title}")
print(f"         success_metrics={kpi_count} | timeline_phases={steps_count}")
print()

# Test 5: Finalize
r5 = requests.post(f"{base}/finalize", json={"domain": "finance", "use_case_id": 2})
fin = r5.json()
print(f"[TEST 5] finalize: {fin['use_case']['title']}")
print(f"         message: {fin['confirmation_message'][:60]}")
print()

print("=" * 50)
all_ok = r1.ok and r2.ok and r3.ok and r4.ok and r5.ok
print(f"ALL TESTS {'PASSED' if all_ok else 'FAILED'}")
