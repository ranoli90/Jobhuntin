import requests


def get_data():
    api_token = "rnd_V3u4rM4GNZcTQXSWUzNjv375AVdY"
    service_id = "srv-d66aadsr85hc73dastfg"
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    headers = {"Authorization": f"Bearer {api_token}"}
    r = requests.get(url, headers=headers)
    print(r.text)


if __name__ == "__main__":
    get_data()
