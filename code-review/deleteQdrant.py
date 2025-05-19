import requests

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "conventions"

response = requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")

if response.ok:
    print("✅ 컬렉션 전체 삭제 완료!")
else:
    print("❌ 삭제 실패:", response.text)