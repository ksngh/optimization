import requests
from sentence_transformers import SentenceTransformer

qdrant_url = "http://localhost:6333"
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

rules = [
    "클래스 이름은 UpperCamelCase로 작성해야 합니다.",
    "인터페이스 이름은 '-able' 접미사를 사용하여 동작을 표현해야 합니다.",
    "메서드 이름은 동사로 시작하고 camelCase로 작성해야 합니다.",
    "숫자 상수는 의미 있는 이름으로 static final로 선언해야 합니다.",
    "하드코딩된 문자열은 상수나 설정 파일로 분리해야 합니다.",
    "if 문에는 항상 중괄호를 사용해야 합니다.",
    "한 줄은 120자를 넘기지 않아야 합니다.",
    "Boolean 변수는 'is', 'has' 등의 접두어로 시작해야 합니다.",
    "Controller에서는 Entity를 직접 반환하지 않고 DTO로 매핑해야 합니다.",
    "Null 대신 Optional을 반환하는 것이 좋습니다.",
    "catch 블록에서는 반드시 예외를 로깅해야 합니다.",
    "중첩된 if 문은 최대한 피하고, 리팩토링을 고려해야 합니다.",
    "Builder를 사용할 경우 필수 필드는 명확히 지정해야 합니다.",
    "변수 이름은 축약하지 말고, 의미 있는 이름을 작성해야 합니다.",
    "Exception은 무분별하게 throw하지 않고, 의미 있는 커스텀 예외를 사용해야 합니다.",
]


vectors = embedding_model.encode(rules)

points = [
    {
        "id": i,
        "vector": vectors[i].tolist(),
        "payload": {
            "rule": rules[i]
        }
    } for i in range(len(rules))
]

# Qdrant에 업로드
requests.put(f"{qdrant_url}/collections/conventions", json={
    "vectors": {"size": 384, "distance": "Cosine"},
    "optimizers_config": {"default_segment_number": 1}
})

requests.put(f"{qdrant_url}/collections/conventions/points", json={
    "points": points
})
