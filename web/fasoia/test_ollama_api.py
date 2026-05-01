import requests

# Tester l'API Ollama
response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'gemma2:2b',
        'prompt': 'Dis "Ollama API fonctionne"',
        'stream': False
    }
)

print(response.json()['response'])