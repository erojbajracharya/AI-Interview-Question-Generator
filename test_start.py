import requests, json, sys
payload = {
    "candidate_id": 1,
    "role_key": "software_engineer",
    "difficulty": "intermediate",
    "num_questions": 5,
    "source": "ai",
    "save_to_db": False,
    "api_keys": "",
    "experience_years": 2,
    "hard_skills": [],
    "soft_skills": []
}
try:
    resp = requests.post('http://localhost:5000/api/interview/start', json=payload)
    print('Status:', resp.status_code)
    print('Response:', resp.text)
except Exception as e:
    print('Error:', e)
    sys.exit(1)
