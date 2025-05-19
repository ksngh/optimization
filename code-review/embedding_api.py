from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "conventions"

embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o-mini")

app = Flask(__name__)

def fetch_convention_rules(vector):
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
        json={
            "vector": vector,
            "top": 5,
            "with_payload": True
        }
    )
    if not response.ok:
        return None, response.text

    rules = []
    result = response.json().get("result", [])
    for match in result:
        rule = match["payload"].get("rule")
        if rule:
            rules.append(rule)
    return rules, None


@app.route("/embed", methods=["POST"])
def embed():
    text = request.json.get("text")
    if not text:
        return jsonify({"error": "리뷰할 코드가 누락되었습니다."}), 400

    # 벡터 생성
    vector = embedding_model.embed_query(text)

    # 컨벤션 검색
    rules, error = fetch_convention_rules(vector)
    if error:
        return jsonify({"error": "Qdrant 검색 실패", "detail": error}), 500

    # 프롬프트 구성
    prompt = f"""
    {rules}는 컨벤션입니다. 
    {text} 
    컨벤션에 맞게 위 코드를 최대한 자세하게 리뷰하세요.
    문제점이 없는 부분은 리뷰하지 마세요.
    다음은 피드백 순서 및 카테고리입니다.
    - **Observation**: 코드에서 관찰된 사실
    - **Interpretation**: 해석 및 위험 가능성
    - **Suggestion**: 개선 방안 제안
    해당 내용에 맞게 리뷰하세요.
    """

    # 메시지 구성
    messages = [
        SystemMessage(content="당신은 전문 코드 리뷰어 AI입니다. "),
        HumanMessage(content=prompt)
    ]

    # LLM 응답
    response = llm.invoke(messages)
    print(rules)
    print(response.content)
    prompt02 = f"""
    이전 단계에서 생성된 리뷰 내용을 아래에 제공합니다. 이 리뷰는 코드에 대한 초기 분석으로 구성되어 있으며, 항목별로 Observation, Interpretation, Suggestion이 포함되어 있을 수 있습니다.
    중요도가 높은 순서대로 최대 5개까지 정리하여 주세요. 리뷰는 존댓말로 하세요.
    
    **[L0-리뷰불가]**

    - PR Description, 테크 스펙 등 어떤 작업을 했는지 충분한 설명이 없는 경우
    - 변경 작업이 너무 커서 리뷰가 어려운 경우
    - 설계가 잘못되어 전체적으로 재작업이 필요하다고 판단해 리뷰를 진행할 수 없는 경우
    
    **[L1-변경요청]**
    
    - 기능 결함, 심각한 퀄리티 저하, 팀 컨벤션 위반 등 반드시 머지 전에 변경이 필요한 경우
    
    **[L2-변경협의]**
    
    - 가급적 머지 전에 변경되었으면 좋겠지만, 배포 후 후속작업으로 바로 진행이 된다면 괜찮다고 생각하는 경우
    - 작성자가 의견에 동의하지 않는다면 토론 필요
    
    **[L3-중요질문]**
    
    - 궁금증이 해소되어야 정확한 리뷰/피드백이 가능하다고 판단하는 경우
    
    **[L4-변경제안]**
    
    - 제시한 방안이 더 좋다고 생각하지만 작성자 판단에 맡겨도 무관한 경우
    
    **[L5-참고의견]**
    
    - 더 좋은지는 모르겠으나 다른 방법 제시 혹은 참고할만한 내용인 경우

    ---
    ## 🔍 Review Format

    ### Feedback (1~n)

    ### [번호]. 요약 제목
    - **Observation**: 코드에서 관찰된 사실
    - **Interpretation**: 해석 및 위험 가능성
    - **Suggestion**: 개선 방안 제안
    - **Review Level**: [Lx: 등급명]

    ---
    ## 📋 Final Checklist

    - [ ] L1~L2 등급에 해당하는 수정 요청 항목
    - ( ) L3~L5 등급에 해당하는 선택적 제안 항목

    다음은 원본 리뷰입니다:

    {response.content}
    """

    response02 = llm.invoke([
        SystemMessage(content="당신은 리뷰 결과를 요약하고 정리하는 템플릿 마스터입니다. 당신의 역할은 다음과 같습니다: 1. 리뷰 항목을 각각 식별하여, 2. 형식에 맞게 정돈하고, 3. 각 항목에 대해 L0~L5 등급 중 하나를 부여하는 것입니다."),
        HumanMessage(content=prompt02)
    ])

    return response02.content

if __name__ == "__main__":
    app.run(port=5001)
