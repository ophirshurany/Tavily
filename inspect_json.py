import json

try:
    with open('data/summaries_1k.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            item = data[0]
        elif isinstance(data, dict) and "data" in data:
            item = data["data"][0]
        else:
            print("Unknown structure")
            exit()
            
        print("Keys:", list(item.keys()))
        print("Sample Item:", json.dumps(item, indent=2)[:500]) # First 500 chars
except Exception as e:
    print(e)
