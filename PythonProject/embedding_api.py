from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
app = Flask(__name__)

@app.route("/embed", methods=["POST"])
def embed():
    text = request.json["text"]
    vector = model.encode(text).tolist()
    return jsonify({"embedding": vector})

if __name__ == "__main__":
    app.run(port=5001)