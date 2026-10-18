import requests
import json
import sys

BASE = "http://localhost:8000"

def test_pipeline():
    print("=" * 60)
    print("TESTING FULL PIPELINE")
    print("=" * 60)

    # 1. Upload dataset
    print("\n[1] Uploading dataset...")
    try:
        with open("sample-data/sales.csv", "rb") as f:
            resp = requests.post(f"{BASE}/upload", files={"file": ("sales.csv", f, "text/csv")})
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ERROR: {resp.text}")
            return
        upload_data = resp.json()
        file_id = upload_data["file_id"]
        print(f"   file_id: {file_id}")
        print(f"   rows: {upload_data['profile']['rows']}")
        print(f"   columns: {upload_data['profile']['columns']}")
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        return

    # 2. Analyze (create plan + hypotheses)
    print("\n[2] Creating analysis plan & hypotheses...")
    goal = "Analyze why sales vary across regions and identify key drivers"
    try:
        resp = requests.post(f"{BASE}/analyze", json={"file_id": file_id, "goal": goal})
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ERROR: {resp.text}")
            return
        analyze_data = resp.json()
        session_id = analyze_data["session_id"]
        plan = analyze_data["analysis_plan"]
        hypotheses = analyze_data["hypotheses"]
        print(f"   session_id: {session_id}")
        print(f"   plan steps: {len(plan.get('steps', []))}")
        print(f"   hypotheses: {len(hypotheses)}")
        for h in hypotheses[:3]:
            print(f"     - {h.get('id')}: {h.get('statement', '')[:80]}")
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        return

    # 3. Execute
    print("\n[3] Executing analysis tools...")
    try:
        resp = requests.post(f"{BASE}/execute", json={"session_id": session_id})
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ERROR: {resp.text}")
            return
        exec_data = resp.json()
        results = exec_data["execution_results"]
        print(f"   execution results: {len(results)}")
        for r in results[:5]:
            print(f"     - {r.get('step_id')}: {r.get('status')} | {r.get('description', '')[:60]}")
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        return

    # 4. Verify
    print("\n[4] Verifying results...")
    try:
        resp = requests.post(f"{BASE}/verify", json={"session_id": session_id})
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ERROR: {resp.text}")
            return
        verify_data = resp.json()
        v = verify_data["verification"]
        print(f"   verified: {v.get('verified')}")
        print(f"   confidence: {v.get('overall_confidence')}")
        print(f"   issues: {len(v.get('issues', []))}")
        for issue in v.get("issues", [])[:3]:
            print(f"     - {issue.get('type')}: {issue.get('message', '')[:80]}")
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        return

    # 5. Report
    print("\n[5] Generating report...")
    try:
        resp = requests.post(f"{BASE}/report", json={"session_id": session_id})
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ERROR: {resp.text}")
            return
        report_data = resp.json()
        report = report_data["report"]
        print(f"   report keys: {list(report.keys())}")
        print(f"   findings: {len(report.get('key_findings', []))}")
        print(f"   visualizations: {len(report.get('visualizations', []))}")
        print(f"   confidence: {report.get('confidence', {})}")
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        return

    # 6. Session state
    print("\n[6] Checking session state...")
    try:
        resp = requests.get(f"{BASE}/session/{session_id}")
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ERROR: {resp.text}")
            return
        session = resp.json()
        print(f"   status: {session.get('status')}")
        print(f"   completed_steps: {session.get('completed_steps')}")
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        return

    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
