import requests

class EmailVerifier:
    @staticmethod
    def verify(email):
        if email.endswith(".edu"):
            return True

        API_URL = "https://api.zerobounce.net/v2/validate"
        API_KEY = "4664d857b775436fb8680d75fd495460"

        params = {
            "api_key": API_KEY,
            "email": email
        }

        try:
            response = requests.get(API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "valid"
        except Exception as e:
            print(f"ZeroBounce verification failed: {e}")

        return False
