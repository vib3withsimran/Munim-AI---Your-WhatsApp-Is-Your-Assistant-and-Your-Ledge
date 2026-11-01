import json

with open(r'C:\Users\Mahima\.gemini\antigravity\brain\f3878317-669f-409c-be12-d297406f1deb\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            step = data.get('step_index')
            content = data.get('content', '')
            media = data.get('media', [])
            print(f"=== USER INPUT step {step} ===")
            safe_content = content[:300].encode('ascii', errors='replace').decode('ascii')
            print("Content:", safe_content)
            print("Media:", len(media))
