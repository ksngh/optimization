package com.smartfintech.codereview.controller;

import com.smartfintech.codereview.ReviewRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.ai.ollama.OllamaChatModel;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.Objects;

@RestController
@RequiredArgsConstructor
public class ReviewController {

    private final OllamaChatModel model;
    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping("/review")
    public String review(@RequestBody ReviewRequest request) {
        // 1. 코드 → 임베딩
        Map<String, String> body = Map.of("text", request.getCode());
        HttpEntity<Map<String, String>> req = new HttpEntity<>(body);
        String url = "http://localhost:5001/embed";
        Map<String, Object> response = restTemplate.postForObject(url, req, Map.class);
        List<Double> embedding = (List<Double>) response.get("embedding");

        // 2. Qdrant 검색 (Top-5 유사 규칙 가져오기)
        String searchBody = """
                {
                    "vector": %s,
                    "top": 5,
                    "with_payload": true
                }
                """.formatted(embedding.toString());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<String> qdrantReq = new HttpEntity<>(searchBody, headers);

        Map result = restTemplate.postForObject("http://localhost:6333/collections/conventions/points/search", qdrantReq, Map.class);
        List<Map> results = (List<Map>) result.get("result");

        System.out.println("🔍 Qdrant 검색 결과: ");
        results.forEach(a -> {
            System.out.println("▶️ " + a);
        });

        // 3. 규칙 추출
        List<String> rules = results.stream()
                .map(rulesResult -> {
                    Map payload = (Map) rulesResult.get("payload");
                    if (payload != null && payload.get("rule") != null) {
                        return payload.get("rule").toString();
                    } else {
                        return null;
                    }
                })
                .filter(Objects::nonNull)
                .toList();

        // 4. LLM 프롬프트 구성 + 리뷰 요청
        String prompt = """
                아래 자바 코드를 다음 컨벤션에 따라 리뷰해줘.
                
                코드:
                %s
                
                컨벤션:
                %s
                """.formatted(request.getCode(), String.join("\n", rules));
        String modelResult = model.call(prompt);
        System.out.println(modelResult);
        return modelResult;
    }
}