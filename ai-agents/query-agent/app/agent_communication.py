import requests


def send_to_agent_2(data):

    response = requests.post(
        "http://localhost:8002/analyze",
        json=data,
        timeout=10
    )

    response.raise_for_status()

    return response.json()