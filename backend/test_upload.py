import requests
import os

# Test file path
test_file = '../sample-data/sales.csv'

if os.path.exists(test_file):
    print(f"Testing upload with: {test_file}")
    
    with open(test_file, 'rb') as f:
        files = {'file': ('sales.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8000/upload', files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
else:
    print(f"Test file not found: {test_file}")
