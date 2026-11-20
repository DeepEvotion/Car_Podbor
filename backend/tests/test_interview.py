from backend.app import interview


def test_ai_cannot_modify_constraints_and_only_generates_known_questions(monkeypatch):
    monkeypatch.setattr(interview, "complete", lambda payload: ({
        "summary": "Нужна машина для семьи",
        "preferences": {"useCases": ["family"], "mustHave": ["awd"], "budget": {"max": 1}},
        "questions": [
            {"key": "luggageClass", "title": "Берёте ли вы чемоданы в дальние поездки?"},
            {"key": "luggageClass", "title": "Повторный вопрос о вещах"},
            {"key": "email", "title": "Как с вами связаться?"},
        ],
    }, "ok"))
    result = interview.interview("Ездим семьёй", initial=True)
    assert result["provider"] == "ai"
    assert result["profile"]["useCases"] == ["family"]
    assert result["profile"]["mustHave"] == []
    assert result["profile"]["budget"]["status"] == "unknown"
    assert [question["key"] for question in result["questions"]] == ["luggageClass"]


def test_fallback_adapts_to_completed_answers(monkeypatch):
    monkeypatch.setattr(interview, "complete", lambda payload: (None, "not_configured"))
    result = interview.interview("", {"useCases": ["family"], "passengers": 5}, ("useCases", "passengers"))
    assert result["provider"] == "deterministic"
    assert [question["key"] for question in result["questions"]] == ["luggageClass", "budget"]


def test_family_and_electric_descriptions_produce_different_questions(monkeypatch):
    monkeypatch.setattr(interview, "complete", lambda payload: (None, "unreachable"))
    family = interview.interview("Ездим с ребёнком, возим коляску на дачу", initial=True)
    electric = interview.interview("Хочу электромобиль для города", initial=True)
    assert family["aiStatus"] == electric["aiStatus"] == "unreachable"
    assert "семейные поездки" in family["summary"]
    assert family["questions"][0]["key"] == "passengers"
    assert family["questions"][1]["key"] == "luggageClass"
    assert electric["profile"]["powertrain"] == "electric"
    assert "электромобиль" in electric["summary"]
    assert electric["questions"][0]["key"] == "powertrain"


def test_remote_questions_receive_latest_answers_and_cannot_repeat(monkeypatch):
    def provider(payload):
        assert payload["answers"] == {"luggageClass": "large"}
        return {"questions": [
            {"key": "luggageClass", "title": "Сколько вещей вам нужно?"},
            {"key": "passengers", "title": "Сколько человек поедет с большим багажом?"},
        ]}, "ok"

    monkeypatch.setattr(interview, "complete", provider)
    result = interview.interview("Хочу машину для поездок", {"luggageClass": "large", "passengers": 5}, ["luggageClass"])
    assert result["provider"] == "ai"
    assert result["questions"] == [{"key": "passengers", "title": "Сколько человек поедет с большим багажом?"}]


def test_network_block_is_reported_separately(monkeypatch):
    class Blocked(OSError):
        winerror = 10013

    class Opener:
        def open(self, *args, **kwargs):
            raise Blocked()

    monkeypatch.setattr(interview, "build_opener", lambda *args, **kwargs: Opener())
    monkeypatch.setenv("AI_CHAT_URL", "https://example.com/v1/chat/completions")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setenv("AI_API_KEY", "test-key")
    assert interview.complete({}) == (None, "network_blocked")

