import os
import json
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "conventions"
EMBEDDING_MODEL = "text-embedding-3-small"
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "static", "code_convention_rules.json")

with open(json_path, "r", encoding="utf-8") as f:
    raw_rules = json.load(f)

rules_text = [item["rule"] for item in raw_rules]

qdrant_client = QdrantClient(url=QDRANT_URL)

try:
    existing = qdrant_client.get_collection(COLLECTION_NAME)
    print("🧹 기존 컬렉션 삭제")
    qdrant_client.delete_collection(COLLECTION_NAME)
except UnexpectedResponse:
    print("📦 컬렉션이 존재하지 않습니다")

qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embedding=embeddings,
)

vectorstore.add_texts(texts=rules_text)

print("Qdrant 업로드 완료")
