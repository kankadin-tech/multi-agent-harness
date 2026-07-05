# Shared Learnings

작업 완료 후 재사용 가능한 교훈만 추가한다. 평소 append-only. 중복·일회성·작업 특화 내용은 기록하지 않는다.

## 분류 규칙

- **시스템 운영 자체**에 대한, 어떤 작업에든 적용되는 교훈 → 이 파일 (`_shared/learnings.md`).
- **특정 외부 프로젝트/repo에 묶인** 교훈 → `_local/learnings.md` (git 추적 안 함, 명시 요청 없이는 로드하지 않음).

## 통합 패스 (성장 관리)

이 파일이 20KB(`wc -c`)를 넘으면 다음 시스템 수정 작업에서 통합 패스를 수행한다:
- 반복 검증된 교훈은 해당 규칙 파일(routing.md·orchestrator-rules.md 등)로 승격
- 승격된 항목은 본문에서 제거하고, 파일 말미 "## 통합됨" 섹션에 1줄 요약 + 승격처 경로만 남긴다
- 통합 패스는 시스템 수정 작업이므로 orchestrator-rules §2 프로토콜(수정 → check-invariants.sh)을 따른다

## 형식

```
## [YYYY-MM-DD] [작업명]
**교훈**: 한 문장. 다음 작업에 그대로 적용 가능한 형태로.
**근거**: 왜 그런지, 어떤 작업에서 발견했는지.
**worker**: [관련 worker명 또는 orchestrator]
```

---

<!-- 이 아래부터 교훈 추가 -->

## [2026-06-01] [antigravity-flavor]
**교훈**: Antigravity(Gemini)가 Orchestrator인 flavor에서는 산출물 리뷰 worker를 Gemini(오케스트레이터) 자기검수로 두지 말고 `codex-critic`으로 분리해야 독립 검토의 의미가 유지된다.
**근거**: 사용자 결정에 따라 원본 MultiAgent의 critic 역할을 Antigravity 버전에 맞게 재설계했다.
**worker**: orchestrator
