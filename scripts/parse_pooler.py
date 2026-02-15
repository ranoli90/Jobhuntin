import json

PASSWORD = "ravhuv-gitqec-nixvY4"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        with open(path, "r", encoding="utf-16") as f:
            return json.load(f)

try:
    data = load_json("pooler_config.json")
    conn_str = None
    if isinstance(data, list):
        for item in data:
            if "connection_string" in item:
                conn_str = item["connection_string"]
                break

    if conn_str:
        final_conn_str = conn_str.replace("[YOUR-PASSWORD]", PASSWORD)
        print(final_conn_str)
    else:
        print("Error: No connection string found")
except Exception as e:
    print(f"Error parsing: {e}")
