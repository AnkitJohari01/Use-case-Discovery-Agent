import requests
import sys

base = "http://localhost:8000"
domains = ["music industry", "space exploration", "agriculture"]
results = {}

sys.stdout.reconfigure(encoding="utf-8")

def test_diversity():
    print("Testing Case Study Diversification...\n")
    
    for domain in domains:
        print(f"Querying domain: '{domain}'")
        res = requests.get(f"{base}/discover", params={"domain": domain})
        
        if res.status_code != 200:
            print(f"  Error: HTTP {res.status_code}")
            sys.exit(1)
            
        data = res.json()
        use_cases = data.get("use_cases", [])
        
        titles = [uc["title"] for uc in use_cases]
        results[domain] = titles
        
        print(f"  Received {len(use_cases)} case studies")
        for i, t in enumerate(titles[:2]): # print first two for brevity
            print(f"  {i+1}. {t}")
        if len(titles) > 2:
            print(f"  ... and {len(titles)-2} more")
        print()

    print("Verifying Diversity:")
    # Check if any two domains received the exact same list of case studies (length and order)
    pairs = [(0,1), (0,2), (1,2)]
    diversity_passed = True
    for i, j in pairs:
        d1, d2 = domains[i], domains[j]
        l1, l2 = results[d1], results[d2]
        
        # Check if lists are identical
        if l1 == l2:
            print(f"  FAIL: '{d1}' and '{d2}' received the EXACT same case studies.")
            diversity_passed = False
        else:
            print(f"  PASS: '{d1}' and '{d2}' generated different sets of case studies.")

    # Check varying lengths
    lengths = set([len(v) for v in results.values()])
    if len(lengths) > 1:
        print(f"  PASS: Found varying lengths of generated lists: {lengths}")
    else:
        print(f"  NOTE: All lists had length {lengths.pop()}, which is possible due to random chance, but keep an eye out if this persists.")

    if diversity_passed:
        print("\n✅ DIVERSITY TEST PASSED")
    else:
        print("\n❌ DIVERSITY TEST FAILED")

if __name__ == "__main__":
    test_diversity()
