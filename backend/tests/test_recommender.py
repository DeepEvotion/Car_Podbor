from backend.app.recommender import (
    apply_duel_choice,
    choose_duel,
    default_profile,
    normalize_profile,
    parse_free_text,
    recommend,
)


def test_must_have_is_applied_before_ranking():
    profile = default_profile()
    profile.update({"useCases": ["city"], "mustHave": ["electric"]})
    result = recommend(profile)
    assert result["candidates"]
    assert all(candidate["car"]["facts"]["powertrain"] == "electric" for candidate in result["candidates"])


def test_unknown_budget_does_not_exclude_candidates():
    profile = default_profile()
    profile.update({"useCases": ["city"], "budget": {"status": "unknown"}})
    result = recommend(profile)
    assert result["status"] == "complete"
    assert len(result["candidates"]) == 5


def test_same_profile_is_stable():
    profile = default_profile()
    profile.update({"useCases": ["travel"], "passengers": 5, "mustHave": ["five_seats"]})
    first = [candidate["carId"] for candidate in recommend(profile)["candidates"]]
    second = [candidate["carId"] for candidate in recommend(profile)["candidates"]]
    assert first == second


def test_normalization_deduplicates_answers():
    profile = normalize_profile({"useCases": ["city", "city"], "mustHave": ["automatic", "automatic"], "style": {"brightness": 2}})
    assert profile["useCases"] == ["city"]
    assert profile["mustHave"] == ["automatic"]
    assert profile["style"]["brightness"] == 1


def test_strict_conflict_returns_no_matches():
    profile = default_profile()
    profile.update({"mustHave": ["electric", "seven_seats", "manual"]})
    assert recommend(profile)["status"] == "no_matches"


def test_budget_max_and_passenger_count_filter_every_mode():
    profile = {"passengers": 5, "budget": {"max": 2_000_000, "status": "provided"}}
    for mode in ("balance", "heart", "reasonable"):
        result = recommend(profile, mode=mode)
        assert result["candidates"]
        for candidate in result["candidates"]:
            facts = candidate["car"]["facts"]
            assert facts["seats"] >= 5
            assert facts["price"]["min"] <= 2_000_000


def test_unknown_mandatory_fact_excludes_car(monkeypatch):
    from backend.app import recommender

    candidate = {**recommender.CATALOG[0], "facts": {"drive": "unknown"}}
    monkeypatch.setattr(recommender, "CATALOG", [candidate])
    result = recommend({"mustHave": ["awd"]})
    assert result["status"] == "no_matches"
    assert result["excluded"][0]["reasons"] == [{"requirement": "awd", "status": "unknown"}]


def test_duels_keep_constraints_use_distinct_pairs_and_learn_by_focus():
    profile = {"mustHave": ["automatic"], "passengers": 5}
    allowed = {candidate["carId"] for candidate in recommend(profile, limit=100)["candidates"]}
    pairs = set()
    for answer in ("left", "both", "none"):
        profile, duel = choose_duel(profile)
        assert duel is not None
        pair = frozenset((duel["left"]["id"], duel["right"]["id"]))
        assert pair not in pairs and pair <= allowed
        pairs.add(pair)
        style = profile["style"].copy()
        profile = apply_duel_choice(profile, duel, answer)
        changed = {key for key in style if style[key] != profile["style"][key]}
        assert changed == ({duel["focus"]["key"]} if answer != "none" else set())
    assert choose_duel(profile)[1] is None
    assert profile["mustHave"] == ["automatic"]


def test_text_parser_only_infers_a_preference():
    profile = parse_free_text("Автомат для города и путешествий, 5 мест, полный привод")
    assert profile["useCases"] == ["city", "travel"]
    assert profile["passengers"] == 5
    assert profile["transmission"] == "automatic"
    assert profile["answerStatuses"]["passengers"] == "inferred"
    assert profile["niceToHave"] == ["awd"]
    assert not profile["mustHave"]
