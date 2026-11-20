"""Deterministic recommendation engine used by the demo API and tests."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

CATALOG_VERSION = "local-2026-01"
ALGORITHM_CONFIG = {"version": "mvp-0.3", "tradeoffPenaltyPerItem": 0.018, "maxTradeoffPenalty": 0.18,
                    "weights": {"rational": 0.55, "emotional": 0.30, "completeness": 0.15}}
ALGORITHM_VERSION = ALGORITHM_CONFIG["version"]
WEIGHTS = ALGORITHM_CONFIG["weights"]
REQUIREMENT_LABELS = {
    "automatic": "автоматическая коробка", "manual": "механическая коробка",
    "five_seats": "от пяти мест", "seven_seats": "от семи мест", "awd": "полный привод",
    "high_clearance": "клиренс от 190 мм", "electric": "электромобиль", "hybrid": "гибрид",
    "diesel": "дизель", "large_luggage": "большой багажник",
}

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "catalog.json"
with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
    CATALOG: list[dict[str, Any]] = json.load(catalog_file)
from .catalog_extra import build_catalog
CATALOG.extend(build_catalog())


def default_profile() -> dict[str, Any]:
    return {
        "profileVersion": 2,
        "sourceText": "",
        "useCases": [],
        "passengers": None,
        "luggageClass": None,
        "roadConditions": [],
        "transmission": None,
        "powertrain": None,
        "budget": {"min": None, "max": None, "status": "unknown"},
        "mustHave": [],
        "niceToHave": [],
        "style": {
            "brightness": None,
            "modernity": None,
            "comfort": None,
            "sportiness": None,
            "practicality": None,
            "status": None,
            "compactness": None,
            "technology": None,
            "retro": None,
        },
        "duelHistory": [],
        "uncertainties": [],
        "answerStatuses": {},
        "priorities": {"economy": None, "reliability": None, "safety": None, "parking": None, "maintenance": None, "longTrips": None, "eco": None},
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    normalized = default_profile()
    if profile:
        normalized.update({key: value for key, value in profile.items() if value is not None})
    normalized["useCases"] = list(dict.fromkeys(str(value) for value in _as_list(normalized.get("useCases"))))
    normalized["roadConditions"] = list(dict.fromkeys(str(value) for value in _as_list(normalized.get("roadConditions"))))
    normalized["mustHave"] = list(dict.fromkeys(str(value) for value in _as_list(normalized.get("mustHave"))))
    normalized["niceToHave"] = list(dict.fromkeys(str(value) for value in _as_list(normalized.get("niceToHave"))))
    passengers = normalized.get("passengers")
    normalized["passengers"] = int(passengers) if str(passengers).isdigit() else None
    if normalized["passengers"] is not None and not 1 <= normalized["passengers"] <= 20:
        raise ValueError("Invalid passenger count")
    if normalized["luggageClass"] not in (None, "small", "medium", "large"):
        raise ValueError("Invalid luggage class")
    budget = normalized.get("budget") or {}
    normalized["budget"] = {
        "min": int(budget["min"]) if str(budget.get("min", "")).isdigit() else None,
        "max": int(budget["max"]) if str(budget.get("max", "")).isdigit() else None,
        "status": budget.get("status") or ("provided" if budget.get("min") or budget.get("max") else "unknown"),
    }
    budget = normalized["budget"]
    if budget["status"] == "provided":
        if budget["min"] is None and budget["max"] is None:
            budget["status"] = "unknown"
        if budget["min"] is not None and budget["max"] is not None and budget["min"] > budget["max"]:
            raise ValueError("Invalid budget range")
    style = normalized.get("style") or {}
    normalized["style"] = {
        key: (max(0, min(1, float(style[key]))) if style.get(key) is not None else None)
        for key in default_profile()["style"]
    }
    priorities = normalized.get("priorities") or {}
    normalized["priorities"] = {key: (max(0, min(1, float(priorities[key]))) if priorities.get(key) is not None else None)
                                 for key in default_profile()["priorities"]}
    return normalized


def _fact(car: dict[str, Any], key: str) -> Any:
    return (car.get("facts") or {}).get(key)


def _requirement(car: dict[str, Any], requirement: str) -> bool | None:
    facts = car.get("facts") or {}
    if requirement in {"automatic", "auto"}:
        value = facts.get("transmission")
        return None if value in (None, "unknown") else value in {"automatic", "robot", "cvt"}
    if requirement == "manual":
        value = facts.get("transmission")
        return None if value in (None, "unknown") else value == "manual"
    if requirement in {"five_seats", "5_seats"}:
        return None if facts.get("seats") is None else facts["seats"] >= 5
    if requirement in {"seven_seats", "7_seats"}:
        return None if facts.get("seats") is None else facts["seats"] >= 7
    if requirement in {"awd", "four_wheel_drive"}:
        value = facts.get("drive")
        return None if value in (None, "unknown") else value == "awd"
    if requirement in {"high_clearance", "high_ground_clearance"}:
        value = facts.get("clearanceMm")
        return None if value is None else value >= 190
    if requirement in {"electric", "ev"}:
        value = facts.get("powertrain")
        return None if value in (None, "unknown") else value == "electric"
    if requirement == "hybrid":
        value = facts.get("powertrain")
        return None if value in (None, "unknown") else value == "hybrid"
    if requirement == "diesel":
        value = facts.get("powertrain")
        return None if value in (None, "unknown") else value == "diesel"
    if requirement in {"large_luggage", "big_luggage"}:
        luggage = facts.get("luggageClass")
        return None if luggage is None else luggage == "large"
    return None


def check_eligibility(car: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    checks = []
    for requirement in profile["mustHave"]:
        result = _requirement(car, requirement)
        checks.append({"requirement": requirement, "status": "unknown" if result is None else ("passed" if result else "failed")})
    if profile["passengers"] is not None:
        seats = _fact(car, "seats")
        status = "unknown" if seats is None else ("passed" if seats >= profile["passengers"] else "failed")
        checks.append({"requirement": "passengers", "status": status})
    if profile["budget"]["status"] == "provided":
        price = _fact(car, "price")
        status = "unknown" if price is None else ("passed" if budget_matches(price, profile["budget"]) else "failed")
        checks.append({"requirement": "budget", "status": status})
    return {"eligible": all(check["status"] == "passed" for check in checks), "checks": checks}


def budget_matches(price, budget):
    low, high = budget.get("min"), budget.get("max")
    return (low is None or price["max"] >= low) and (high is None or price["min"] <= high)


def preference_confidence(profile: dict[str, Any]) -> float:
    """How much of the decision is known; used to avoid fake precision."""
    fields = [
        bool(profile.get("useCases")), profile.get("passengers") is not None,
        bool(profile.get("luggageClass")), bool(profile.get("roadConditions")),
        bool(profile.get("transmission")), bool(profile.get("powertrain")),
        (profile.get("budget") or {}).get("status") == "provided",
        bool(profile.get("mustHave") or profile.get("niceToHave")),
        any(value is not None for value in (profile.get("style") or {}).values()),
        any(value is not None for value in (profile.get("priorities") or {}).values()),
    ]
    return sum(fields) / len(fields)


def _segment(car: dict[str, Any]) -> str:
    facts = car.get("facts") or {}
    return facts.get("bodyType") or "unknown"


def _luggage_score(car: dict[str, Any], requested: str | None) -> float:
    if not requested:
        return 0.5
    order = {"small": 1, "medium": 2, "large": 3}
    actual = _fact(car, "luggageClass")
    if actual not in order:
        return 0.0
    delta = order[actual] - order[requested]
    return 1.0 if delta >= 0 else max(0.0, 1 + delta * 0.5)


def rational_score(car: dict[str, Any], profile: dict[str, Any]) -> tuple[float, list[str], list[str], list[str]]:
    scores: list[float] = []
    matched: list[str] = []
    tradeoffs: list[str] = []
    unknown: list[str] = []
    priorities = profile.get("priorities") or {}
    facts = car.get("facts") or {}
    # Soft needs turn an apparently generic request into a personal ranking.
    priority_scores = {
        "economy": 1 - min(1, float(facts.get("price", {}).get("min", 0)) / 10000000),
        "reliability": float((car.get("suitability") or {}).get("work", .5)),
        "safety": .9 if facts.get("seats", 0) >= 5 else .55,
        "parking": float((car.get("style") or {}).get("compactness", .5)),
        "maintenance": .85 if facts.get("powertrain") in {"petrol", "diesel"} else .65,
        "longTrips": float((car.get("suitability") or {}).get("highway", .5)),
        "eco": 1.0 if facts.get("powertrain") == "electric" else (.8 if facts.get("powertrain") == "hybrid" else .35),
    }
    for key, requested in priorities.items():
        if requested is None:
            continue
        score = 1 - abs(priority_scores[key] - requested)
        scores.append(score * .8)
        priority_names = {"economy": "экономичности", "reliability": "надёжности", "safety": "безопасности", "parking": "парковке", "maintenance": "стоимости обслуживания", "longTrips": "дальним поездкам", "eco": "экологичности"}
        if score >= .7:
            matched.append(f"подходит по приоритету «{priority_names.get(key, key)}»")
        elif score < .45:
            tradeoffs.append(f"компромисс по приоритету «{priority_names.get(key, key)}»")
    use_cases = profile["useCases"]
    if use_cases:
        use_score = sum(float((car.get("suitability") or {}).get(use_case, 0.0)) for use_case in use_cases) / len(use_cases)
        scores.append(use_score)
        if use_score >= 0.65:
            matched.append("подходит под ваш сценарий использования")
        elif use_score < 0.45:
            tradeoffs.append("сценарий использования совпадает частично")
    passengers = profile.get("passengers")
    if passengers:
        seats = _fact(car, "seats")
        if seats is None:
            unknown.append("данные о количестве мест не подтверждены")
            scores.append(0.0)
        else:
            seat_score = 1.0 if seats >= passengers else max(0.0, seats / passengers)
            scores.append(seat_score)
            if seats >= passengers:
                matched.append(f"вмещает нужное количество пассажиров ({seats} мест)")
            else:
                tradeoffs.append(f"мест меньше, чем требуется ({seats} против {passengers})")
    if profile.get("luggageClass"):
        luggage_score = _luggage_score(car, profile["luggageClass"])
        scores.append(luggage_score)
        if _fact(car, "luggageClass") is None:
            unknown.append("вместимость багажника не указана")
        elif luggage_score >= 0.95:
            matched.append("багажник соответствует выбранному объёму")
        elif luggage_score < 0.75:
            tradeoffs.append("багажник меньше желаемого")
    if profile.get("roadConditions"):
        suitability = car.get("suitability") or {}
        road_score = sum(float(suitability.get(condition, 0.0)) for condition in profile["roadConditions"]) / len(profile["roadConditions"])
        scores.append(road_score)
        if road_score >= 0.65:
            matched.append("подходит для выбранных дорожных условий")
        elif road_score < 0.45:
            tradeoffs.append("проходимость или трассовый комфорт ниже запроса")
    transmission = profile.get("transmission")
    if transmission and transmission not in {"any", "unknown"}:
        actual = _fact(car, "transmission")
        if actual is None or actual == "unknown":
            unknown.append("коробка передач не подтверждена")
            scores.append(0.0)
        else:
            matched_transmission = actual == transmission or (transmission == "automatic" and actual in {"automatic", "robot", "cvt"})
            scores.append(1.0 if matched_transmission else 0.0)
            (matched if matched_transmission else tradeoffs).append("коробка передач соответствует запросу" if matched_transmission else "коробка передач отличается от предпочтения")
    powertrain = profile.get("powertrain")
    if powertrain and powertrain not in {"any", "unknown"}:
        actual = _fact(car, "powertrain")
        if actual is None or actual == "unknown":
            unknown.append("тип силовой установки не подтверждён")
            scores.append(0.0)
        else:
            matches = actual == powertrain
            scores.append(1.0 if matches else 0.0)
            (matched if matches else tradeoffs).append("тип силовой установки совпадает" if matches else "тип силовой установки отличается")
    budget = profile.get("budget") or {}
    if budget.get("status") == "provided" and (budget.get("min") or budget.get("max")):
        price = _fact(car, "price")
        if not price:
            unknown.append("цена не подтверждена")
            scores.append(0.0)
        else:
            low, high = budget.get("min"), budget.get("max")
            matches = budget_matches(price, budget)
            budget_score = float(matches)
            if matches and low is not None and high is not None and high > low:
                budget_score = (min(price["max"], high) - max(price["min"], low)) / (high - low)
            scores.append(budget_score)
            if matches:
                matched.append("диапазон цены пересекается с вашим бюджетом")
            else:
                tradeoffs.append("цена выходит за указанный бюджет")
    for requirement in profile["niceToHave"]:
        result = _requirement(car, requirement)
        label = REQUIREMENT_LABELS.get(requirement, requirement)
        if result is True:
            matched.append(f"выполняется пожелание «{label}»")
            scores.append(1.0)
        elif result is False:
            tradeoffs.append(f"пожелание «{label}» не выполнено")
            scores.append(0.0)
        else:
            unknown.append(f"пожелание «{label}» нельзя проверить по каталогу")
    return (sum(scores) / len(scores) if scores else 0.5, matched, tradeoffs, unknown)


def emotional_score(car: dict[str, Any], profile: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    requested = profile.get("style") or {}
    distances = []
    matched: list[str] = []
    tradeoffs: list[str] = []
    labels = {"brightness": ("сдержанный", "яркий"), "modernity": ("классический", "современный"), "comfort": ("более строгий", "уютный"), "sportiness": ("спокойный", "спортивный"), "practicality": ("ориентированный на эмоции", "практичный"), "compactness": ("основательный", "компактный"), "technology": ("простой", "технологичный"), "retro": ("современный", "ретро"), "status": ("неформальный", "статусный")}
    for key, value in requested.items():
        if value is None:
            continue
        actual = (car.get("style") or {}).get(key)
        if actual is None:
            continue
        closeness = 1 - abs(actual - value)
        distances.append(closeness)
        low_label, high_label = labels.get(key, (key, key))
        label = high_label if value >= 0.6 else low_label
        if closeness >= 0.7:
            matched.append(f"по редакционной оценке близок выбранный стиль: {label}")
        else:
            tradeoffs.append(f"по редакционной оценке стиль отличается от выбранного: {label}")
    return (sum(distances) / len(distances) if distances else 0.5, matched, tradeoffs)


def completeness_score(car: dict[str, Any], profile: dict[str, Any]) -> float:
    relevant = ["seats", "luggageClass", "transmission", "powertrain", "price"]
    if profile.get("passengers") is None:
        relevant.remove("seats")
    if profile.get("luggageClass") is None:
        relevant.remove("luggageClass")
    if not profile.get("transmission"):
        relevant.remove("transmission")
    if not profile.get("powertrain"):
        relevant.remove("powertrain")
    if (profile.get("budget") or {}).get("status") != "provided":
        relevant.remove("price")
    if not relevant:
        return 1.0
    facts = car.get("facts") or {}
    return sum(1 for key in relevant if facts.get(key) not in (None, "unknown")) / len(relevant)


def recommend(profile: dict[str, Any], limit: int = 5, mode: str = "balance") -> dict[str, Any]:
    profile = normalize_profile(profile)
    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for car in CATALOG:
        eligibility = check_eligibility(car, profile)
        if not eligibility["eligible"]:
            excluded.append({"carId": car["id"], "reasons": [check for check in eligibility["checks"] if check["status"] != "passed"]})
            continue
        rational, rational_matched, rational_tradeoffs, rational_unknown = rational_score(car, profile)
        emotional, emotional_matched, emotional_tradeoffs = emotional_score(car, profile)
        completeness = completeness_score(car, profile)
        confidence = preference_confidence(profile)
        # With a vague brief, do not pretend style is as important as practical
        # fit. With a detailed brief, emotional preferences can meaningfully
        # separate otherwise suitable cars.
        rational_weight = 0.68 - confidence * 0.10
        emotional_weight = 0.17 + confidence * 0.20
        completeness_weight = 1 - rational_weight - emotional_weight
        final = rational_weight * rational + emotional_weight * emotional + completeness_weight * completeness
        tradeoff_penalty = min(ALGORITHM_CONFIG["maxTradeoffPenalty"], len(rational_tradeoffs + emotional_tradeoffs) * ALGORITHM_CONFIG["tradeoffPenaltyPerItem"])
        final = max(0.0, final - tradeoff_penalty)
        matched = rational_matched + emotional_matched
        matched.extend(f"в каталоге указано обязательное условие «{REQUIREMENT_LABELS.get(key, key)}»" for key in profile["mustHave"])
        tradeoffs = rational_tradeoffs + emotional_tradeoffs
        unknown = rational_unknown
        candidates.append({"carId": car["id"], "car": car, "eligibility": eligibility, "scores": {"rational": round(rational, 4), "emotional": round(emotional, 4), "completeness": round(completeness, 4), "final": round(final, 4)}, "matched": matched[:4], "tradeoffs": tradeoffs[:4], "unknown": unknown[:3]})
    mode_score = {"balance": "final", "reasonable": "rational", "heart": "emotional"}[mode]
    candidates.sort(key=lambda candidate: (-candidate["scores"][mode_score], -candidate["scores"]["final"], candidate["carId"]))
    distinct = {}
    for candidate in candidates:
        car = candidate["car"]
        distinct.setdefault((car["brand"].casefold(), car["model"].casefold()), candidate)
    candidates = list(distinct.values())
    for index, candidate in enumerate(candidates):
        candidate["rank"] = index + 1
        candidate["labels"] = ["balance"]
        if candidate["scores"]["rational"] >= candidate["scores"]["emotional"]:
            candidate["labels"].append("reasonable")
        if candidate["scores"]["emotional"] >= candidate["scores"]["rational"]:
            candidate["labels"].append("heart")
    # Return a useful shortlist rather than five near-identical cars: first
    # take the strongest model from each body type, then fill by score.
    selected = []
    used_segments = set()
    for candidate in candidates:
        segment = _segment(candidate["car"])
        if segment not in used_segments or len(selected) >= max(3, limit - 2):
            selected.append(candidate)
            used_segments.add(segment)
        if len(selected) == limit:
            break
    for candidate in candidates:
        if len(selected) == limit:
            break
        if candidate not in selected:
            selected.append(candidate)
    for index, candidate in enumerate(selected):
        alternative = next(iter(candidates[index + 1:index + 2] or candidates[index - 1:index]), None)
        if alternative:
            car = alternative["car"]
            candidate["alternative"] = {key: car[key] for key in ("id", "brand", "model")}
            candidate["alternative"]["bodyType"] = _fact(car, "bodyType")
    status = "complete" if selected else "no_matches"
    exclusions = Counter(check["requirement"] for car in excluded for check in car["reasons"])
    confidence = preference_confidence(profile)
    return {"id": str(uuid4()), "profile": profile, "catalogVersion": CATALOG_VERSION, "algorithmVersion": ALGORITHM_VERSION,
            "status": status, "mode": mode, "preferenceConfidence": round(confidence, 2),
            "candidates": selected, "excluded": excluded, "topConstraints": dict(exclusions.most_common()), "totalCandidates": len(candidates)}


def parse_free_text(text: str) -> dict[str, Any]:
    """Deterministic fallback for the AI adapter. It only emits known enum values."""
    profile = default_profile()
    clean = text[:2000].lower().replace("ё", "е")
    profile["sourceText"] = text[:2000] if text else ""
    priority_signals = {
        "economy": ["эконом", "расход", "дешев", "топливо"],
        "reliability": ["надёж", "надеж", "безотказ"],
        "safety": ["безопас", "детей", "семь"],
        "parking": ["парков", "компакт", "узк", "маленьк"],
        "maintenance": ["обслужив", "ремонт", "запчаст"],
        "longTrips": ["дальн", "трасс", "путешеств"],
        "eco": ["эколог", "электр", "гибрид", "заряд"],
    }
    for key, needles in priority_signals.items():
        if any(needle in clean for needle in needles):
            profile["priorities"][key] = 0.9
    mappings = {
        "city": ["город", "пробк", "парков", "по городу"],
        "work": ["работ", "развоз", "доставк"],
        "travel": ["путешеств", "дальн", "поездк"],
        "family": ["семь", "детей", "ребен", "детск", "коляск"],
        "poorRoads": ["грунт", "бездорож", "дачу", "даче", "дачн", "снег", "сугроб", "рыбалк", "просел"],
        "highway": ["трасс", "шоссе"],
    }
    for value, needles in mappings.items():
        if any(needle in clean for needle in needles):
            profile["useCases" if value in {"city", "travel", "family", "work"} else "roadConditions"].append(value)
    if re.search(r"\b(?:автомат|акпп|вариатор|робот\w* коробк)\w*\b", clean):
        profile["transmission"] = "automatic"
    elif re.search(r"\b(?:механик\w*|мкпп)\b", clean):
        profile["transmission"] = "manual"
    if re.search(r"электромобил|электрокар|на электричестве|электрическую машину", clean):
        profile["powertrain"] = "electric"
    elif "гибрид" in clean:
        profile["powertrain"] = "hybrid"
    elif "дизел" in clean:
        profile["powertrain"] = "diesel"
    elif "бензин" in clean:
        profile["powertrain"] = "petrol"
    match = re.search(r"(\d+)\s*(?:человек|пассажир|мест)", clean)
    if match and len(match.group(1)) <= 2 and 1 <= int(match.group(1)) <= 20:
        profile["passengers"] = int(match.group(1))
    if any(word in clean for word in ["большой багаж", "много вещей", "чемодан", "коляск", "велосипед"]):
        profile["luggageClass"] = "large"
    elif any(word in clean for word in ["немного вещей", "небольшой багаж"]):
        profile["luggageClass"] = "small"
    if any(word in clean for word in ["высокий клиренс", "бездорож"]):
        profile["niceToHave"].append("high_clearance")
    if "полный привод" in clean:
        profile["niceToHave"].append("awd")
    for key, cues in {
        "brightness": ("ярк", "необычн"), "sportiness": ("спортивн", "динамичн"),
        "compactness": ("компактн", "небольшая машина", "парков"), "comfort": ("уютн", "комфорт"),
        "technology": ("технологич", "футурист"), "retro": ("ретро", "винтаж"),
    }.items():
        if any(cue in clean for cue in cues):
            profile["style"][key] = 0.8
            profile["answerStatuses"][key] = "inferred"
    for key in ("useCases", "passengers", "luggageClass", "roadConditions", "transmission", "powertrain", "niceToHave"):
        profile["answerStatuses"][key] = "inferred" if profile[key] else "unknown"
    return normalize_profile(profile)


DUEL_DIMENSIONS = {
    "brightness": ("Сдержанная внешность", "Яркая внешность"),
    "comfort": ("Более строгий образ", "Уютный образ"),
    "sportiness": ("Спокойный характер", "Спортивный характер"),
    "compactness": ("Основательный формат", "Компактный формат"),
    "practicality": ("Акцент на эмоциях", "Акцент на практичности"),
    "technology": ("Более простой образ", "Технологичный образ"),
    "retro": ("Более современный образ", "Акцент на ретро"),
}


def choose_duel(profile: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    result = recommend(profile, limit=12)
    profile = result["profile"]
    history = profile["duelHistory"]
    if len(history) >= 3:
        return profile, None
    used_pairs = {frozenset(entry["pair"]) for entry in history}
    used_dimensions = {entry["focus"] for entry in history}
    ranked = result["candidates"]
    best_score = 0.0
    best = None
    for index, first in enumerate(ranked):
        for second in ranked[index + 1 :]:
            left, right = first["car"], second["car"]
            if frozenset((left["id"], right["id"])) in used_pairs:
                continue
            relevance = 0.5 + (first["scores"]["final"] + second["scores"]["final"]) / 4
            for key, labels in DUEL_DIMENSIONS.items():
                left_value, right_value = left["style"].get(key), right["style"].get(key)
                if key in used_dimensions or left_value is None or right_value is None:
                    continue
                difference = abs(left_value - right_value)
                uncertainty = 1.0 if profile["style"][key] is None else 0.55
                score = difference * relevance * uncertainty
                if difference >= 0.18 and score > best_score:
                    best_score = score
                    left_label, right_label = labels if left_value < right_value else labels[::-1]
                    best = {
                        "left": {key: left[key] for key in ("id", "brand", "model")},
                        "right": {key: right[key] for key in ("id", "brand", "model")},
                        "focus": {"key": key, "leftLabel": left_label, "rightLabel": right_label},
                    }
    return profile, best


def apply_duel_choice(profile: dict[str, Any], duel: dict[str, Any], choice: str):
    key = duel["focus"]["key"]
    pair = [duel[side]["id"] for side in ("left", "right")]
    cars = {car["id"]: car for car in CATALOG}
    if choice in {"left", "right", "both"}:
        left, right = (cars[car_id]["style"][key] for car_id in pair)
        target = {"left": left, "right": right, "both": (left + right) / 2}[choice]
        rate = 0.05 if choice == "both" else (0.15, 0.12, 0.08)[len(profile["duelHistory"])]
        current = profile["style"][key]
        current = 0.5 if current is None else current
        profile["style"][key] = round(current + rate * (target - current), 4)
        profile["answerStatuses"][key] = "inferred"
    profile["duelHistory"].append({"choice": choice, "pair": pair, "focus": key})
    return profile
