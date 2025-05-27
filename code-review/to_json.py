import json

# 전체 diff 텍스트를 문자열로 저장 (사용자가 제공한 텍스트 그대로)
full_diff_text = '''
diff --git a/src/main/java/com/sft/investor/application/resolver/mutation/VulMutationResolver.java b/src/main/java/com/sft/investor/application/resolver/mutation/VulMutationResolver.java
index b0f3b0f9..83b4e4ac 100644
--- a/src/main/java/com/sft/investor/application/resolver/mutation/VulMutationResolver.java
+++ b/src/main/java/com/sft/investor/application/resolver/mutation/VulMutationResolver.java
@@ -6,6 +6,7 @@
 import com.sft.investor.application.dto.vul.VulSearchHistoryCreateInput;
 import com.sft.investor.common.annotation.Authenticated;
 import com.sft.investor.config.security.user.AuthUser;
+import com.sft.investor.domain.invest.request.FixedTypeToggleUpdate;
 import com.sft.investor.domain.invest.service.InvestCustomerService;
 import com.sft.investor.domain.invest.service.VulCacheService;
 import com.sft.investor.domain.invest.service.VulService;
@@ -79,6 +80,19 @@ public Boolean updateVulCustomerGoodsToggle(
         return investCustomerService.toggleCustomerFund(input.toCustomerGoodsUpdate());
     }
 
+    /**
+     * 변액보험 - 비교, 관심, 거치적립 토글 저장 및 삭제
+     */
+    @Authenticated(userType = UserType.INSURANCE)
+    @MutationMapping
+    public Boolean updateVulFixedTypesToggle(
+            @Argument FixedTypeToggleUpdate input,
+            @AuthenticationPrincipal AuthUser authUser
+    ) {
+        Long userIdx = getUserIdx(authUser);
+        return vulCacheService.toggleFixedType(userIdx, input);
+    }
+
     private static Long getUserIdx(AuthUser authUser) {
         if (authUser == null) throw new SessionExpiredException();
         return authUser.getUserIdx();
diff --git a/src/main/java/com/sft/investor/application/resolver/query/VulQueryResolver.java b/src/main/java/com/sft/investor/application/resolver/query/VulQueryResolver.java
index 469aed5e..e64dbabf 100644
--- a/src/main/java/com/sft/investor/application/resolver/query/VulQueryResolver.java
+++ b/src/main/java/com/sft/investor/application/resolver/query/VulQueryResolver.java
@@ -103,8 +103,8 @@ public VulFixedGoodsResponse vulFixedGoodsList(
             @Argument FixedType type
     ) {
         Long userIdx = getUserIdx(authUser);
-        List<VulFixedGoodsInfo> responses = vulUseCase.getFixedGoodsInfo(userIdx, type);
-        return new VulFixedGoodsResponse(responses);
+        List<VulFixedGoodsInfo> response = vulUseCase.getFixedGoodsInfo(userIdx, type);
+        return new VulFixedGoodsResponse(response);
     }
 
     /** 변액보험 - 그래프 다중 조회 (펀드비교) */
diff --git a/src/main/java/com/sft/investor/application/usecase/VulUseCase.java b/src/main/java/com/sft/investor/application/usecase/VulUseCase.java
index e24f6456..84574009 100644
--- a/src/main/java/com/sft/investor/application/usecase/VulUseCase.java
+++ b/src/main/java/com/sft/investor/application/usecase/VulUseCase.java
@@ -2,14 +2,14 @@
 
 import com.sft.investor.annotation.UseCase;
 import com.sft.investor.application.GoodsType;
-import com.sft.investor.application.response.FundInfo;
-import com.sft.investor.domain.invest.response.*;
 import com.sft.investor.application.dto.vul.VulSearchHistoryInfo;
+import com.sft.investor.application.response.FundInfo;
 import com.sft.investor.application.response.GoodsInfo;
 import com.sft.investor.application.response.GraphInfo;
 import com.sft.investor.domain.invest.FixedType;
 import com.sft.investor.domain.invest.request.FundGraphRequest;
 import com.sft.investor.domain.invest.request.MaGraphRequest;
+import com.sft.investor.domain.invest.response.*;
 import com.sft.investor.domain.invest.service.InvestCustomerService;
 import com.sft.investor.domain.invest.service.VulService;
 import com.sft.investor.domain.mygps.response.CustomerHaving;
@@ -30,18 +30,18 @@ public class VulUseCase {
     private final InvestCustomerService investCustomerService;
 
     /**
-     *  변액보험 - 상품검색 목록 조회
-     *  1. 검색 히스토리
-     *  2. 고객의 보유 상품 조회
-     *  3. 본인의 비교, 관심, 적립 상품 조회
-     *  4. 펀드 상세 조회
+     * 변액보험 - 상품검색 목록 조회
+     * 1. 검색 히스토리
+     * 2. 고객의 보유 상품 조회
+     * 3. 본인의 비교, 관심, 적립 상품 조회
+     * 4. 펀드 상세 조회
      */
     public List<VulSearchHistoryInfo> getSearchHistories(Long userIdx, List<GoodsInfo> goodsInfos, Long customerIdx) {
 
         // 고객 보유 상품 정보 조회
         Map<String, Boolean> customerGoodsMap = Collections.emptyMap();
 
-        if(customerIdx != null) {
+        if (customerIdx != null) {
             CustomerHaving customerHaving = investCustomerService.getCustomerHavingList(customerIdx, GoodsType.VUL);
 
             if (customerHaving != null) {
@@ -82,24 +82,14 @@ public List<VulSearchHistoryInfo> getSearchHistories(Long userIdx, List<GoodsInf
                 .toList();
     }
 
+    /**
+     * 변액보험 - 비교, 관심, 거치적립 조회 (메뉴별 리스트 조회)
+     * 1. 상품 조회
+     * 2. 타입 별 토글 목록 조회
+     * 3. 토글 목록과 상품 목록 비교 후 반환
+     */
     public List<VulFixedGoodsInfo> getFixedGoodsInfo(Long userIdx, FixedType type) {
-        List<GoodsInfo> goodsInfos = vulService.getUserFixedGoodsList(userIdx, type);
-
-        if (goodsInfos == null) {
-            return Collections.emptyList();
-        }
-
-        return goodsInfos.stream()
-                .map(goodsInfo -> {
-                    List<VulFundInfo> vulFundInfos = vulService.getVulFundList(goodsInfo.getCompanyName(), goodsInfo.getGoodsName());
-
-                    return new VulFixedGoodsInfo(
-                            goodsInfo.getCompanyName(),
-                            goodsInfo.getGoodsName(),
-                            vulFundInfos
-                    );
-                })
-                .toList();
+        return vulService.getUserFixedGoodsList(userIdx, type);
     }
 
     public List<VulHavingGoodsInfo> getCustomerHavingGoodsInfo(Long customerIdx) {
@@ -112,10 +102,10 @@ public List<VulHavingGoodsInfo> getCustomerHavingGoodsInfo(Long customerIdx) {
 
         Map<String, Set<String>> customerFundMap = customerHaving.getFundList() != null
                 ? customerHaving.getFundList().stream()
-                    .collect(Collectors.groupingBy(
-                            FundInfo::getGoodsName,
-                            Collectors.mapping(FundInfo::getFundName, Collectors.toSet())
-                    ))
+                .collect(Collectors.groupingBy(
+                        FundInfo::getGoodsName,
+                        Collectors.mapping(FundInfo::getFundName, Collectors.toSet())
+                ))
                 : Collections.emptyMap();
 
         return customerHaving.getGoodsList().stream()
@@ -141,7 +131,7 @@ public List<VulHavingGoodsInfo> getCustomerHavingGoodsInfo(Long customerIdx) {
 
     public List<GraphInfo> getGraphInfoList(FixedType fixedType, String code, LocalDateTime startDate, LocalDateTime endDate, Integer days) {
         if (days == null) {
-            if(fixedType == FixedType.COMPARISON) {
+            if (fixedType == FixedType.COMPARISON) {
                 return vulService.getVulFundDetailPercentByFundCode(new FundGraphRequest(code, startDate.toLocalDate(), endDate.toLocalDate()));  // 퍼센트 그래프
             } else {
                 return vulService.getVulFundDetailByFundCode(new FundGraphRequest(code, startDate.toLocalDate(), endDate.toLocalDate()));  // 비교 그래프
@@ -149,4 +139,5 @@ public List<GraphInfo> getGraphInfoList(FixedType fixedType, String code, LocalD
         }
         return vulService.getVulMADetailByFundCode(new MaGraphRequest(code, startDate.toLocalDate(), endDate.toLocalDate(), days));
     }
+
 }
diff --git a/src/main/java/com/sft/investor/config/db/RedisConfig.java b/src/main/java/com/sft/investor/config/db/RedisConfig.java
index 34a915cf..402f82c7 100644
--- a/src/main/java/com/sft/investor/config/db/RedisConfig.java
+++ b/src/main/java/com/sft/investor/config/db/RedisConfig.java
@@ -1,6 +1,7 @@
 package com.sft.investor.config.db;
 
 import com.fasterxml.jackson.databind.ObjectMapper;
+import com.sft.investor.domain.invest.vo.UserFixedType;
 import lombok.RequiredArgsConstructor;
 import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
 import org.springframework.context.annotation.Bean;
@@ -13,6 +14,7 @@
 import org.springframework.data.redis.core.RedisTemplate;
 import org.springframework.data.redis.listener.RedisMessageListenerContainer;
 import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
+import org.springframework.data.redis.serializer.Jackson2JsonRedisSerializer;
 import org.springframework.data.redis.serializer.JdkSerializationRedisSerializer;
 import org.springframework.data.redis.serializer.StringRedisSerializer;
 
@@ -23,6 +25,23 @@ public class RedisConfig {
 
     private final ObjectMapper objectMapper;
 
+    @Bean
+    public RedisTemplate<String, UserFixedType> userFixedTypeRedisTemplate(RedisConnectionFactory factory) {
+        RedisTemplate<String, UserFixedType> template = new RedisTemplate<>();
+        template.setConnectionFactory(factory);
+
+        template.setKeySerializer(new StringRedisSerializer());
+        Jackson2JsonRedisSerializer<UserFixedType> valueSerializer =
+                new Jackson2JsonRedisSerializer<>(UserFixedType.class);
+        template.setValueSerializer(valueSerializer);
+
+        template.setHashKeySerializer(new StringRedisSerializer());
+        template.setHashValueSerializer(valueSerializer);
+
+        template.afterPropertiesSet();
+        return template;
+    }
+
     @Bean
     public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory factory) {
         RedisTemplate<String, Object> template = new RedisTemplate<>();
diff --git a/src/main/java/com/sft/investor/domain/invest/request/FixedTypeToggleUpdate.java b/src/main/java/com/sft/investor/domain/invest/request/FixedTypeToggleUpdate.java
new file mode 100644
index 00000000..b7a18d06
--- /dev/null
+++ b/src/main/java/com/sft/investor/domain/invest/request/FixedTypeToggleUpdate.java
@@ -0,0 +1,9 @@
+package com.sft.investor.domain.invest.request;
+
+import com.sft.investor.domain.invest.FixedType;
+
+public record FixedTypeToggleUpdate(String goodsName,
+                                    String fundCode,
+                                    FixedType fixedType) {
+
+}
diff --git a/src/main/java/com/sft/investor/domain/invest/response/VulFundInfo.java b/src/main/java/com/sft/investor/domain/invest/response/VulFundInfo.java
index a2502967..5a250cbc 100644
--- a/src/main/java/com/sft/investor/domain/invest/response/VulFundInfo.java
+++ b/src/main/java/com/sft/investor/domain/invest/response/VulFundInfo.java
@@ -1,5 +1,7 @@
 package com.sft.investor.domain.invest.response;
 
+import lombok.AccessLevel;
+import lombok.AllArgsConstructor;
 import lombok.Getter;
 import lombok.ToString;
 
@@ -8,30 +10,32 @@
 
 @Getter
 @ToString
+@AllArgsConstructor(access = AccessLevel.PRIVATE)
 public class VulFundInfo {
 
-    private LocalDate baseDate;
-    private String companyName;
-    private String fundCode;
-    private String fundName;
-    private LocalDate settingDate;
-    private Double presentPrice;
-    private Double annualIncome;
-    private Double remuneration;
-    private String type;
-    private String goodsName;
+    private final LocalDate baseDate;
+    private final String companyName;
+    private final String fundCode;
+    private final String fundName;
+    private final LocalDate settingDate;
+    private final Double presentPrice;
+    private final Double annualIncome;
+    private final Double remuneration;
+    private final String type;
+    private final String goodsName;
+    private Boolean toggle;
 
     public VulFundInfo(
-        String baseDate,
-        String companyName,
-        String fundCode,
-        String fundName,
-        String settingDate,
-        Double presentPrice,
-        String annualIncome,
-        Double remuneration,
-        String type,
-        String goodsName
+            String baseDate,
+            String companyName,
+            String fundCode,
+            String fundName,
+            String settingDate,
+            Double presentPrice,
+            String annualIncome,
+            Double remuneration,
+            String type,
+            String goodsName
     ) {
         this.baseDate = LocalDate.parse(baseDate, DateTimeFormatter.ofPattern("yyyyMMdd"));
         this.companyName = companyName;
@@ -43,5 +47,24 @@ public VulFundInfo(
         this.remuneration = remuneration;
         this.type = type;
         this.goodsName = goodsName;
+        this.toggle = false;
     }
+
+    public VulFundInfo withToggle() {
+        return new VulFundInfo(
+                this.baseDate,
+                this.companyName,
+                this.fundCode,
+                this.fundName,
+                this.settingDate,
+                this.presentPrice,
+                this.annualIncome,
+                this.remuneration,
+                this.type,
+                this.goodsName,
+                true
+        );
+    }
+
+
 }
diff --git a/src/main/java/com/sft/investor/domain/invest/service/VulCacheService.java b/src/main/java/com/sft/investor/domain/invest/service/VulCacheService.java
index 492dc993..cf9cdae6 100644
--- a/src/main/java/com/sft/investor/domain/invest/service/VulCacheService.java
+++ b/src/main/java/com/sft/investor/domain/invest/service/VulCacheService.java
@@ -2,23 +2,69 @@
 
 import com.sft.investor.common.exception.grapql.CustomException;
 import com.sft.investor.common.exception.grapql.ErrorCode;
+import com.sft.investor.domain.invest.FixedType;
+import com.sft.investor.domain.invest.entity.FixedGoods;
+import com.sft.investor.domain.invest.request.FixedTypeToggleUpdate;
+import com.sft.investor.domain.invest.vo.UserFixedType;
 import io.micrometer.common.util.StringUtils;
 import lombok.RequiredArgsConstructor;
 import lombok.extern.slf4j.Slf4j;
 import org.springframework.data.redis.core.BoundListOperations;
+import org.springframework.data.redis.core.BoundSetOperations;
+import org.springframework.data.redis.core.RedisTemplate;
 import org.springframework.data.redis.core.StringRedisTemplate;
 import org.springframework.stereotype.Service;
 
 import java.util.List;
+import java.util.Objects;
+import java.util.Set;
 
 @Slf4j
 @Service
 @RequiredArgsConstructor
 public class VulCacheService {
 
+    private final static String FIXED_TYPE_TOGGLE_KEY = "userFixedTypeToggle";
     private final StringRedisTemplate redisTemplate;
-
     private final String REDIS_KEY = "investor_vul_%s";
+    private final RedisTemplate<String, UserFixedType> objectRedisTemplate;
+
+    public Set<UserFixedType> getUserFixedTypes(Long userIdx, FixedType fixedType) {
+        String redisKey = FIXED_TYPE_TOGGLE_KEY + ":" + userIdx + ":" + fixedType;
+        BoundSetOperations<String, UserFixedType> ops = objectRedisTemplate.boundSetOps(redisKey);
+        return ops.members();
+    }
+
+    public void deleteUserFixedType(Long userIdx, FixedGoods fixedGoods) {
+        String redisKey = FIXED_TYPE_TOGGLE_KEY + ":" + userIdx + ":" + fixedGoods.getFixedType();
+        BoundSetOperations<String, UserFixedType> ops = objectRedisTemplate.boundSetOps(redisKey);
+
+        Set<UserFixedType> members = Objects.requireNonNull(ops.members());
+
+        members.forEach(
+                userFixedType -> {
+                    String userGoodsName = userFixedType.getGoodsName();
+                    String fixedGoodsName = fixedGoods.getGoodsName();
+                    if (userGoodsName.equals(fixedGoodsName)) {
+                        ops.remove(userFixedType);
+                    }
+                }
+        );
+
+    }
+
+    public Boolean toggleFixedType(Long userIdx, FixedTypeToggleUpdate fixedTypeToggleUpdate) {
+        UserFixedType userFixedType = UserFixedType.toggle(fixedTypeToggleUpdate);
+        String redisKey = FIXED_TYPE_TOGGLE_KEY + ":" + userIdx + ":" + userFixedType.getFixedType();
+        Boolean isToggled = objectRedisTemplate.opsForSet().isMember(redisKey, userFixedType);
+        if (Boolean.TRUE.equals(isToggled)) {
+            objectRedisTemplate.opsForSet().remove(redisKey, userFixedType);
+            return false;
+        } else {
+            objectRedisTemplate.opsForSet().add(redisKey, userFixedType);
+            return true;
+        }
+    }
 
     public void setSearchHistoryByUserIdx(Long userIdx, String companyName, String goodsName) {
         if (StringUtils.isBlank(companyName) || StringUtils.isBlank(goodsName)) {
diff --git a/src/main/java/com/sft/investor/domain/invest/service/VulService.java b/src/main/java/com/sft/investor/domain/invest/service/VulService.java
index 63a1abc1..2c84eadc 100644
--- a/src/main/java/com/sft/investor/domain/invest/service/VulService.java
+++ b/src/main/java/com/sft/investor/domain/invest/service/VulService.java
@@ -15,7 +15,9 @@
 import com.sft.investor.domain.invest.request.MaGraphRequest;
 import com.sft.investor.domain.invest.response.FixedGoodsInfo;
 import com.sft.investor.domain.invest.response.FixedGoodsKey;
+import com.sft.investor.domain.invest.response.VulFixedGoodsInfo;
 import com.sft.investor.domain.invest.response.VulFundInfo;
+import com.sft.investor.domain.invest.vo.UserFixedType;
 import com.sft.investor.domain.user.repository.UserRepository;
 import lombok.RequiredArgsConstructor;
 import org.springframework.stereotype.Service;
@@ -36,6 +38,7 @@ public class VulService {
 
     private final VulMapper vulMapper;
     private final UserRepository userRepository;
+    private final VulCacheService vulCacheService;
 
     public List<String> getVulCompanyNames() {
         return vulMapper.findVulCompanyNames();
@@ -118,20 +121,12 @@ public RetentionInfo getVulRetention(FundGraphRequest request) {
                 .build();
     }
 
-    public List<GoodsInfo> getUserFixedGoodsList(Long userIdx, FixedType fixedType) {
+    public List<VulFixedGoodsInfo> getUserFixedGoodsList(Long userIdx, FixedType fixedType) {
         List<FixedGoods> userFixedGoods = getUserFixedGoods(userIdx);
-
-        List<String> goodsNameList = userFixedGoods.stream()
-                .filter(goods -> goods.isMatchedGoods(GoodsType.VUL, fixedType))
-                .sorted(Comparator.comparing(FixedGoods::getCreatedAt).reversed())
-                .map(FixedGoods::getGoodsName)
-                .toList();
-
-        if (goodsNameList.size() == 0) {
-            return null;
-        }
-
-        return vulMapper.findGoodsInfoByGoodsNames(goodsNameList);
+        Set<UserFixedType> userFixedTypes = vulCacheService.getUserFixedTypes(userIdx, fixedType);
+        List<String> goodsNameList = filterGoodsNames(userFixedGoods, fixedType);
+        List<GoodsInfo> goodsInfos = vulMapper.findGoodsInfoByGoodsNames(goodsNameList);
+        return getVulFixedGoodsInfos(goodsInfos, userFixedTypes);
     }
 
     public List<FixedGoodsInfo> getUserFixedGoodsInfo(Long userIdx) {
@@ -159,6 +154,7 @@ public Boolean updateUserFixedGoods(Long userIdx, FixedGoodsUpdate fixedGoodsUpd
 
         if (findGoods.isPresent()) {
             userFixedGoods.remove(findGoods.get());
+            vulCacheService.deleteUserFixedType(userIdx, findGoods.get());
             return false;
         } else {
             FixedGoods fixedGoods = FixedGoods.builder()
@@ -169,6 +165,30 @@ public Boolean updateUserFixedGoods(Long userIdx, FixedGoodsUpdate fixedGoodsUpd
             userFixedGoods.add(fixedGoods);
             return true;
         }
+
+    }
+
+    private List<VulFixedGoodsInfo> getVulFixedGoodsInfos(List<GoodsInfo> goodsInfos, Set<UserFixedType> userFixedTypes) {
+        return goodsInfos.stream()
+                .map(goodsInfo -> {
+                    List<VulFundInfo> updatedFundInfos = getVulFundList(goodsInfo.getCompanyName(), goodsInfo.getGoodsName())
+                            .stream()
+                            .map(vulFundInfo -> toggleIfMatched(userFixedTypes, vulFundInfo))
+                            .sorted(Comparator.comparing(VulFundInfo::getToggle).reversed())
+                            .toList();
+
+                    return new VulFixedGoodsInfo(goodsInfo.getCompanyName(), goodsInfo.getGoodsName(), updatedFundInfos);
+                })
+                .toList();
+    }
+
+    private VulFundInfo toggleIfMatched(Set<UserFixedType> userFixedTypes, VulFundInfo vulFundInfo) {
+        boolean isToggled = userFixedTypes.stream()
+                .anyMatch(userFixed -> userFixed.checkGoodsNameAndFundCode(vulFundInfo));
+        if (isToggled) {
+            return vulFundInfo.withToggle();
+        }
+        return vulFundInfo;
     }
 
     private List<FixedGoods> getUserFixedGoods(Long userIdx) {
@@ -176,5 +196,17 @@ private List<FixedGoods> getUserFixedGoods(Long userIdx) {
                 .orElseThrow(() -> new CustomException(ErrorCode.USER_NOT_FOUND))
                 .getFixedGoodsList();
     }
+
+    private List<String> filterGoodsNames(List<FixedGoods> userFixedGoods, FixedType fixedType) {
+        List<String> goodsNameList = userFixedGoods.stream()
+                .filter(goods -> goods.isMatchedGoods(GoodsType.VUL, fixedType))
+                .sorted(Comparator.comparing(FixedGoods::getCreatedAt).reversed())
+                .map(FixedGoods::getGoodsName)
+                .toList();
+        if (goodsNameList.isEmpty()) {
+            return null;
+        }
+        return goodsNameList;
+    }
 }
 
diff --git a/src/main/java/com/sft/investor/domain/invest/vo/UserFixedType.java b/src/main/java/com/sft/investor/domain/invest/vo/UserFixedType.java
new file mode 100644
index 00000000..8dd13ebb
--- /dev/null
+++ b/src/main/java/com/sft/investor/domain/invest/vo/UserFixedType.java
@@ -0,0 +1,33 @@
+package com.sft.investor.domain.invest.vo;
+
+import com.sft.investor.application.response.GoodsInfo;
+import com.sft.investor.domain.invest.FixedType;
+import com.sft.investor.domain.invest.request.FixedTypeToggleUpdate;
+import com.sft.investor.domain.invest.response.VulFundInfo;
+import lombok.AccessLevel;
+import lombok.AllArgsConstructor;
+import lombok.Getter;
+import lombok.NoArgsConstructor;
+
+@Getter
+@NoArgsConstructor(access = AccessLevel.PROTECTED)
+@AllArgsConstructor(access = AccessLevel.PRIVATE)
+public class UserFixedType {
+
+    private String goodsName;
+    private String fundCode;
+    private FixedType fixedType;
+
+    public static UserFixedType toggle(FixedTypeToggleUpdate fixedTypeToggleUpdate) {
+        return new UserFixedType(fixedTypeToggleUpdate.goodsName(), fixedTypeToggleUpdate.fundCode(), fixedTypeToggleUpdate.fixedType());
+    }
+
+    public static UserFixedType of(GoodsInfo goodsInfo, VulFundInfo vulFundInfo, FixedType fixedType) {
+        return new UserFixedType(goodsInfo.getGoodsName(), vulFundInfo.getFundCode(), fixedType);
+    }
+
+    public boolean checkGoodsNameAndFundCode(VulFundInfo vulFundInfo) {
+        return vulFundInfo.getFundCode().equals(fundCode) && vulFundInfo.getGoodsName().equals(goodsName);
+    }
+
+}
diff --git a/src/main/resources/graphql/schema.graphqls b/src/main/resources/graphql/schema.graphqls
index 59f8e638..42a30b09 100644
--- a/src/main/resources/graphql/schema.graphqls
+++ b/src/main/resources/graphql/schema.graphqls
@@ -181,6 +181,12 @@ type Mutation {
     """
     updateVulCustomerGoodsToggle(input: CustomerGoodsToggleUpdateInput!): Boolean!
 
+    """
+    변액보험 - 비교, 관심, 거치적립 토글 저장 및 삭제
+    (저장 시 true 반환, 삭제 시 false 반환)
+    """
+    updateVulFixedTypesToggle(input: FixedTypeToggleUpdate!): Boolean!
+
     ## Fund (펀드)
     "펀드 - 상품검색 목록 저장"
     createFundSearchHistory(input: FundSearchHistoryCreateInput!): Boolean!
diff --git a/src/main/resources/graphql/types/vul.graphqls b/src/main/resources/graphql/types/vul.graphqls
index d39a9958..19e427e6 100644
--- a/src/main/resources/graphql/types/vul.graphqls
+++ b/src/main/resources/graphql/types/vul.graphqls
@@ -64,6 +64,7 @@ type VulFundInfo {
     remuneration: Float
     type: String!
     goodsName: String!
+    toggle: Boolean!
 }
 
 type VulFundResponse {
@@ -124,6 +125,12 @@ input VulPriceGraphSearchInput {
     endDate: JavaScriptDate!
 }
 
+input FixedTypeToggleUpdate {
+    fixedType: FixedType!
+    goodsName: String!
+    fundCode: String!
+}
+
 input VulMovingAverageGraphSearchInput {
     fundCode: String!
     startDate: JavaScriptDate!
diff --git a/src/test/java/com/sft/investor/application/usecase/VulUseCaseTest.java b/src/test/java/com/sft/investor/application/usecase/VulUseCaseTest.java
index 16eef89c..d21441f5 100644
--- a/src/test/java/com/sft/investor/application/usecase/VulUseCaseTest.java
+++ b/src/test/java/com/sft/investor/application/usecase/VulUseCaseTest.java
@@ -7,6 +7,7 @@
 import com.sft.investor.domain.invest.FixedType;
 import com.sft.investor.domain.invest.response.*;
 import com.sft.investor.domain.invest.service.InvestCustomerService;
+import com.sft.investor.domain.invest.service.VulCacheService;
 import com.sft.investor.domain.invest.service.VulService;
 import com.sft.investor.domain.mygps.response.CustomerHaving;
 import org.junit.jupiter.api.DisplayName;
@@ -31,6 +32,9 @@ class VulUseCaseTest {
     @Mock
     private VulService vulService;
 
+    @Mock
+    private VulCacheService vulCacheService;
+
     @Mock
     private InvestCustomerService investCustomerService;
 
diff --git a/src/test/java/com/sft/investor/domain/invest/service/VulServiceTest.java b/src/test/java/com/sft/investor/domain/invest/service/VulServiceTest.java
index 540c8a67..669fab89 100644
--- a/src/test/java/com/sft/investor/domain/invest/service/VulServiceTest.java
+++ b/src/test/java/com/sft/investor/domain/invest/service/VulServiceTest.java
@@ -9,6 +9,9 @@
 import com.sft.investor.domain.invest.repository.VulMapper;
 import com.sft.investor.domain.invest.request.FixedGoodsUpdate;
 import com.sft.investor.domain.invest.request.FundGraphRequest;
+import com.sft.investor.domain.invest.response.VulFixedGoodsInfo;
+import com.sft.investor.domain.invest.response.VulFundInfo;
+import com.sft.investor.domain.invest.vo.UserFixedType;
 import com.sft.investor.domain.user.entity.User;
 import com.sft.investor.domain.user.repository.UserRepository;
 import org.junit.jupiter.api.DisplayName;
@@ -20,9 +23,12 @@
 import org.mockito.junit.jupiter.MockitoExtension;
 
 import java.time.LocalDate;
+import java.time.LocalDateTime;
+import java.time.Month;
 import java.util.ArrayList;
 import java.util.List;
 import java.util.Optional;
+import java.util.Set;
 
 import static org.assertj.core.api.Assertions.assertThat;
 import static org.mockito.Mockito.*;
@@ -34,6 +40,9 @@ class VulServiceTest {
     @Mock
     private VulMapper vulMapper;
 
+    @Mock
+    private VulCacheService vulCacheService;
+
     @Mock
     private UserRepository userRepository;
 
@@ -97,7 +106,7 @@ void whenGraphDataIsValid_returnCorrectRetentionInfo() {
     class GetUserFixedGoodsList {
 
         @Test
-        @DisplayName("사용자 고정 상품 중 매칭되는 것이 없으면 null 반환")
+        @DisplayName("사용자 fixed goods 중 매칭되는 것이 없으면 null 반환")
         void whenGoodsListIsEmpty_returnNull() {
             //given
             Long userIdx = 1L;
@@ -111,11 +120,60 @@ void whenGoodsListIsEmpty_returnNull() {
             when(userRepository.findById(userIdx)).thenReturn(Optional.of(user));
 
             //when
-            List<GoodsInfo> result = vulService.getUserFixedGoodsList(userIdx, fixedType);
+            List<VulFixedGoodsInfo> result = vulService.getUserFixedGoodsList(userIdx, fixedType);
 
             //then
-            assertThat(result).isNull();
-            verify(vulMapper, never()).findGoodsInfoByGoodsNames(any());
+            assertThat(result).isEmpty();
+        }
+
+        @Test
+        @DisplayName("캐싱된 fundCode와 goodsName이 일치할 시 toggle = true")
+        void whenCachedFundCodeAndGoodsNameMatched_thenToggle() {
+            // given
+            Long userIdx = 1L;
+            FixedType fixedType = FixedType.COMPARISON;
+            String companyName = "삼성생명";
+            String goodsName = "New플래티넘변액연금1.0(무배당) 1종";
+            String fundCode = "KLVL0326320";
+
+            GoodsInfo goodsInfo = new GoodsInfo(companyName, goodsName);
+
+            VulFundInfo vulFundInfo = new VulFundInfo(
+                    "20240510",                     // baseDate
+                    companyName,                   // companyName
+                    fundCode,                      // fundCode
+                    "삼성생명 글로벌채권형",           // fundName
+                    "2022-06-15",                  // settingDate
+                    1000.25,                       // presentPrice
+                    "3.75",                        // annualIncome
+                    0.85,                          // remuneration
+                    fixedType.name(),              // type
+                    goodsName                      // goodsName
+            );
+
+            Set<UserFixedType> userFixedTypes = Set.of(
+                    UserFixedType.of(goodsInfo, vulFundInfo, fixedType)
+            );
+
+            User fakeUser = mock(User.class);
+            when(userRepository.findById(userIdx)).thenReturn(Optional.of(fakeUser));
+            when(fakeUser.getFixedGoodsList()).thenReturn(List.of(mock(FixedGoods.class)));
+            when(vulCacheService.getUserFixedTypes(userIdx, fixedType)).thenReturn(userFixedTypes);
+            when(vulMapper.findGoodsInfoByGoodsNames(any())).thenReturn(List.of(goodsInfo));
+            when(vulMapper.findVulFundList(companyName, goodsName)).thenReturn(List.of(vulFundInfo));
+
+            // when
+            List<VulFixedGoodsInfo> sut = vulService.getUserFixedGoodsList(userIdx, fixedType);
+
+            // then
+            assertThat(sut)
+                    .hasSize(1)
+                    .element(0)
+                    .satisfies(info -> {
+                        assertThat(info.goodsName()).isEqualTo(goodsName);
+                        assertThat(info.companyName()).isEqualTo(companyName);
+                        assertThat(info.vulFundInfos().get(0).getToggle()).isTrue();
+                    });
         }
 
     }
@@ -166,6 +224,7 @@ void whenGoodsNotFixed_thenAddAndReturnTrue() {
             GoodsType goodsType = GoodsType.VUL;
             FixedType fixedType = FixedType.COMPARISON;
 
+
             FixedGoodsUpdate updateDto = new FixedGoodsUpdate(goodsName, goodsType, fixedType);
 
             List<FixedGoods> goodsList = new ArrayList<>();
'''  # 전체 diff는 생략 없이 이어붙이는 것이 이상적이지만, 여기서는 일부만 예시로 작성

# JSON 객체 생성
json_payload = {
    "code": full_diff_text
}

# JSON 문자열로 변환 및 파일 저장
json_str = json.dumps(json_payload, indent=2, ensure_ascii=False)
file_path = "./converted_git_diff.json"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(json_str)
