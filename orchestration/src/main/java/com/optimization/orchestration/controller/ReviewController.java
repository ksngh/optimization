package com.optimization.orchestration.controller;

import com.optimization.orchestration.ReviewRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequiredArgsConstructor
public class ReviewController {

    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping("/review")
    public String review(@RequestBody ReviewRequest request) {
        Map<String, String> body = Map.of("text", request.getCode());
        HttpEntity<Map<String, String>> req = new HttpEntity<>(body);
        String url = "http://localhost:5001/embed";
        return restTemplate.postForObject(url, req, String.class);
    }

}