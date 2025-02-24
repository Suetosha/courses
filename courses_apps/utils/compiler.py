import requests


# Данная функция использует Piston API для обработки кода
def run_code(code):
    try:
        response = requests.post("https://emkc.org/api/v2/piston/execute", json={
            "language": "c++",
            "version": "10.2.0",
            "files": [{"content": code}]
        })

        output = response.json()["run"]["output"].rstrip()
        return output
    except Exception as e:
        return {"error": str(e)}
