import { observePhotos } from "./photos.js";

const STORAGE_KEY = "carmatch-state-v1";
const GARAGE_KEY = "carmatch-garage-v1";

const defaultProfile = () => ({
  profileVersion: 1, sourceText: "", useCases: [], passengers: null, luggageClass: null,
  roadConditions: [], transmission: null, powertrain: null,
  budget: { min: null, max: null, status: "unknown" }, mustHave: [], niceToHave: [],
  style: { brightness: null, modernity: null, comfort: null, sportiness: null, practicality: null, status: null, compactness: null, technology: null, retro: null },
  priorities: { economy: null, reliability: null, safety: null, parking: null, maintenance: null, longTrips: null, eco: null },
  duelHistory: [], uncertainties: [], answerStatuses: {}
});

function readStorage(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

const state = {
  interview: null, profile: defaultProfile(), result: null, testStep: 0, duel: null, links: [], demo: null,
  ...readStorage(STORAGE_KEY, {}),
  garage: readStorage(GARAGE_KEY, []), catalog: [], shared: null, compare: [],
};
state.profile.answerStatuses ??= {};
let busy = false;
let errorMessage = "";

const requirements = { budget: "Бюджет", passengers: "Количество мест", automatic: "Автомат", manual: "Механика", five_seats: "Минимум 5 мест", seven_seats: "Минимум 7 мест", awd: "Полный привод", high_clearance: "Высокий клиренс", electric: "Электромобиль", large_luggage: "Большой багажник", hybrid: "Гибрид" };
const bodies = { hatchback: "хэтчбек", sedan: "седан", wagon: "универсал", crossover: "кроссовер", suv: "внедорожник", minivan: "минивэн", coupe: "купе" };
const labels = { city: "город", highway: "трасса", travel: "путешествия", family: "семья", work: "работа", poorRoads: "плохие дороги" };
const questions = [
  { key: "useCases", title: "Для чего нужна машина?", type: "multi", options: [["city", "Город"], ["highway", "Трасса"], ["travel", "Путешествия"], ["family", "Семья"], ["work", "Работа"]] },
  { key: "passengers", title: "Сколько людей обычно нужно возить?", type: "single", options: [[2, "1–2 человека"], [4, "3–4 человека"], [5, "5 человек"], [7, "6–7 человек"]] },
  { key: "luggageClass", title: "Сколько вещей обычно бывает в поездке?", type: "single", options: [["small", "Немного"], ["medium", "Среднее количество"], ["large", "Много багажа"]] },
  { key: "roadConditions", title: "Где машина будет ездить?", type: "multi", options: [["city", "Город"], ["highway", "Трасса"], ["poorRoads", "Плохие дороги"], ["travel", "Смешанный режим"]] },
  { key: "transmission", title: "Какая коробка передач предпочтительна?", type: "single", options: [["automatic", "Автомат или вариатор"], ["manual", "Механика предпочтительна"], ["any", "Без разницы"]] },
  { key: "powertrain", title: "Какой тип силовой установки рассматривать?", type: "single", options: [["petrol", "Бензин"], ["diesel", "Дизель"], ["hybrid", "Гибрид"], ["electric", "Электромобиль"], ["any", "Без разницы"]] },
  { key: "budget", title: "Какой бюджет заложить?", type: "budget", options: [] },
  { key: "mustHave", title: "Что обязательно должно быть?", type: "multi", options: [["automatic", "Автомат"], ["manual", "Механика"], ["five_seats", "Минимум 5 мест"], ["seven_seats", "7 мест"], ["awd", "Полный привод"], ["high_clearance", "Высокий клиренс"], ["electric", "Электромобиль"], ["large_luggage", "Большой багажник"]] },
  { key: "niceToHave", title: "Что было бы желательно?", type: "multi", options: [["automatic", "Автомат"], ["high_clearance", "Высокий клиренс"], ["awd", "Полный привод"], ["large_luggage", "Большой багажник"], ["electric", "Электромобиль"], ["hybrid", "Гибрид"]] },
  { key: "priorities", title: "Что для вас важнее всего в повседневной жизни?", type: "priority", options: [["economy", "Низкий расход"], ["reliability", "Надёжность"], ["safety", "Безопасность"], ["parking", "Легко парковаться"], ["maintenance", "Недорого обслуживать"], ["longTrips", "Комфорт на трассе"], ["eco", "Экологичность"]] }
];

function persist() {
  const { profile, result, testStep, duel, links, demo, interview } = state;
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ profile, result, testStep, duel, links, demo, interview }));
  if (!demo) localStorage.setItem(GARAGE_KEY, JSON.stringify(state.garage));
}
function esc(value) { return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char])); }
function money(value) { return value ? `${Math.round(value / 1000).toLocaleString("ru-RU")} тыс. ₽` : "не указана"; }
function carById(id) { return state.catalog.find(car => car.id === id); }
function getRoute() { return location.hash.slice(1) || "home"; }
function navigate(route) {
  persist();
  if (getRoute() !== route) history.pushState(null, "", "#" + route);
  render();
  window.scrollTo(0, 0);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(data?.error?.message || "Сервис временно недоступен");
  return data;
}

function post(path, value) {
  return api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
}

async function loadCatalog() {
  const { cars } = await api("/api/catalog");
  state.catalog = cars;
}

async function calculate(mode = "balance") {
  state.result = await post("/api/recommendation", { profile: state.profile, mode });
  navigate("results");
}

function header() {
  return `<header class="topbar"><button class="brand" data-action="home">Автоподбор</button><nav><button data-action="home">Подбор</button><button data-action="garage">Гараж <span class="count">${state.garage.length}</span></button><button data-action="profile">Профиль</button></nav></header>`;
}
function shell(content, title = "") { return `${header()}<main class="container">${title ? `<div class="eyebrow">${esc(title)}</div>` : ""}${content}</main>`; }
function choiceButtons(question) { const value = state.profile[question.key]; return question.options.map(([key, label]) => { const active = question.type === "multi" ? (value || []).includes(key) : question.type === "priority" ? value?.[key] != null : value === key; return `<button class="choice ${active ? "active" : ""}" aria-pressed="${active}" data-choice="${question.key}" data-value="${key}"><span class="choice-mark">${active ? "✓" : ""}</span>${esc(label)}</button>`; }).join(""); }
function renderHome() {
  return shell(`<section class="home-hero"><div class="hero-copy"><div class="eyebrow">Автоподбор, который объясняет выбор</div><h1>Машина должна подходить <em>вашей жизни</em>, а не только фильтрам</h1><p>Опишите задачу обычными словами. Сервис выделит важное, задаст только нужные вопросы и покажет честные компромиссы.</p><div class="hero-proof"><span>60 моделей</span><span>Открытые источники</span><span>Без регистрации</span></div></div><form class="intent-card" id="description-form"><div class="intent-label"><span class="intent-icon">✦</span><div><strong>С чего начнём?</strong><small>Можно написать как другу</small></div></div><textarea id="freeText" maxlength="2000" aria-label="Пожелания к автомобилю" placeholder="Например: езжу по городу, по выходным дача, нужен большой багажник и недорогое обслуживание…">${esc(state.profile.sourceText)}</textarea><button class="primary full" type="submit" data-action="start-text">Разобрать мою задачу <span>→</span></button><div class="intent-divider"><span>или выберите сценарий</span></div><div class="quick-grid"><button type="button" data-quick="city">Город и парковка</button><button type="button" data-quick="family">Семья и поездки</button><button type="button" data-quick="heart">Выбор сердцем</button></div><button class="ghost unknown-start" type="button" data-action="unknown">Не знаю, с чего начать</button></form></section><section class="home-next"><div><span class="eyebrow">Как это работает</span><h2>От жизненной задачи — к подходящему автомобилю</h2></div><div class="steps"><div><b>01</b><strong>Расскажите</strong><span>Что возить, где ездить и что раздражает</span></div><div><b>02</b><strong>Уточним</strong><span>Только вопросы, которые меняют выбор</span></div><div><b>03</b><strong>Объясним</strong><span>Почему машина подходит и где компромисс</span></div></div></section>`);
}

function photo(car, className = "", credit = true) {
  const alt = esc(car.brand + " " + car.model);
  return `<div class="vehicle-photo ${className}" data-photo="${esc(car.id)}" data-alt="${alt}" data-photo-state="loading"><span class="photo-placeholder">Ищем фото ${alt}…</span>${credit ? '<a class="photo-credit" target="_blank" rel="noopener noreferrer" hidden>Фото и лицензия</a>' : ""}</div>`;
}

function activeQuestions() {
  const plan = state.interview?.order;
  if (!plan) return questions;
  return plan.map(({ key, title }) => {
    const question = questions.find(item => item.key === key);
    return { ...question, title: title || question.title };
  });
}

function orderQuestions(proposals, completed = []) {
  const order = [...completed];
  for (const question of [...(Array.isArray(proposals) ? proposals : []), ...questions.map(({ key }) => ({ key }))]) {
    if (!order.some(item => item.key === question.key)) order.push({ key: question.key, title: question.title });
  }
  return order;
}

function interviewIntro() {
  if (state.testStep !== 0 || !state.interview) return "";
  const { summary, provider, aiStatus } = state.interview;
  const status = {
    not_configured: "AI-провайдер не настроен. Вопросы подобраны по локальным правилам.",
    local: "Работает локальный адаптивный интервьюер. Вопросы создаются по вашему описанию.",
    unauthorized: "AI-провайдер отклонил доступ. Вопросы подобраны по локальным правилам.",
    unreachable: "AI-провайдер недоступен. Вопросы подобраны по локальным правилам.",
    network_blocked: "Внешнее соединение с AI заблокировано средой запуска. Вопросы подобраны по локальным правилам.",
    provider_error: "AI-провайдер вернул ошибку. Вопросы подобраны по локальным правилам.",
    invalid_response: "AI-провайдер не вернул вопросы. Вопросы подобраны по локальным правилам.",
  };
  return (summary ? `<p class="interview-summary">${esc(summary)}</p>` : "") +
    `<p class="muted" role="status">${esc(provider === "ai" ? "Вопросы подготовлены AI по вашему запросу." : status[aiStatus] || "Вопросы подобраны по локальным правилам.")}</p>`;
}

function renderTest() {
  const ordered = activeQuestions();
  const total = ordered.length + 1; const question = ordered[state.testStep];
  if (state.testStep >= ordered.length) return renderStyleTest(total);
  const progress = Math.round((state.testStep / total) * 100);
  let body = "";
  if (question.type === "budget") body = `<div class="budget-grid"><label>От, ₽<input id="budgetMin" type="number" min="1" step="1" value="${state.profile.budget.min || ""}" placeholder="не знаю"></label><label>До, ₽<input id="budgetMax" type="number" min="1" step="1" value="${state.profile.budget.max || ""}" placeholder="не знаю"></label></div><button class="choice ${state.profile.budget.status === "unknown" ? "active" : ""}" data-action="budget-unknown">Не знаю или пока не хочу указывать</button>`;
  else body = `<div class="choices ${question.type === "priority" ? "priority-choices" : ""}">${choiceButtons(question)}</div>${question.type === "priority" ? '<p class="muted selection-hint">Можно выбрать несколько приоритетов — остальные останутся нейтральными.</p>' : ""}`;
  return shell(`<div class="progress"><span style="width:${progress}%"></span></div><section class="question"><div class="eyebrow">Шаг ${state.testStep + 1} из ${total}</div><h1>${esc(question.title)}</h1>${interviewIntro()}<p class="muted">Можно выбрать несколько вариантов или пропустить вопрос.</p>${body}<div class="question-actions"><button class="secondary" data-action="back">Назад</button><button class="ghost" data-action="skip">Пропустить</button><button class="primary" data-action="next">Дальше</button></div></section>`);
}

function renderStyleTest(total) {
  const dims = [["brightness", "Сдержанный", "Яркий"], ["modernity", "Ретро", "Современный"], ["comfort", "Строгий", "Уютный"], ["technology", "Простой", "Технологичный"], ["sportiness", "Спокойный", "Спортивный"], ["practicality", "Для удовольствия", "Практичный"], ["status", "Неформальный", "Статусный"], ["compactness", "Основательный", "Компактный"]];
  return shell(`<div class="progress"><span style="width:92%"></span></div><section class="question"><div class="eyebrow">Шаг ${total} из ${total}</div><h1>Какой характер вам ближе?</h1><p class="muted">Эти ответы влияют на эмоциональную часть результата.</p><div class="sliders">${dims.map(([key, low, high]) => `<label><span>${esc(low)}</span><input type="range" min="0" max="1" step="0.05" aria-label="${esc(low)} — ${esc(high)}" data-style="${key}" value="${state.profile.style[key] ?? .5}"><span>${esc(high)}</span></label>`).join("")}</div><div class="question-actions"><button class="secondary" data-action="back">Назад</button><button class="ghost" data-action="skip-style">Пропустить</button><button class="primary" data-action="duels">Перейти к дуэлям</button></div></section>`);
}

function renderDuels() {
  const duel = state.duel;
  if (!duel) return renderTest();
  const { left, right, focus } = duel;
  return shell(`<section class="question"><div class="eyebrow">Дуэль ${state.profile.duelHistory.length + 1} из 3</div><h1>${esc(focus.leftLabel)} или ${esc(focus.rightLabel.toLowerCase())}?</h1><div class="duel"><div>${photo(left)}<button class="duel-card" data-duel="left"><strong>${esc(left.brand)} ${esc(left.model)}</strong><span>${esc(focus.leftLabel)}</span></button></div><div>${photo(right)}<button class="duel-card" data-duel="right"><strong>${esc(right.brand)} ${esc(right.model)}</strong><span>${esc(focus.rightLabel)}</span></button></div></div><div class="duel-actions"><button class="secondary" data-duel="both">Нравятся обе</button><button class="ghost" data-duel="none">Ни одна</button><button class="ghost" data-duel="skip">Пропустить</button><button class="ghost" data-action="finish">К результатам</button></div></section>`);
}

function renderResults() {
  const result = state.result; if (!result) return renderHome();
  const cards = result.candidates || []; const tabs = ["balance", "reasonable", "heart"]; const active = state.result.mode || "balance";
  const confidence = Math.round((result.preferenceConfidence || 0) * 100);
  const lead = cards[0]?.car;
  const leadText = lead ? `Лучшее совпадение — ${lead.brand} ${lead.model}: он закрывает ваши основные задачи, а ниже показаны честные компромиссы.` : "Попробуйте ослабить одно из обязательных ограничений.";
  return shell(`<section class="results-hero"><div><div class="eyebrow">Ваш персональный шорт-лист</div><h1>${cards.length ? `Нашли ${cards.length} машины под вашу жизнь` : "Подходящих моделей пока нет"}</h1><p>${esc(leadText)}</p><div class="confidence"><span>Профиль заполнен на ${confidence}%</span><span class="confidence-bar"><i style="width:${confidence}%"></i></span></div></div><button class="secondary" data-action="edit">Изменить ответы</button></section><div class="mode-tabs">${tabs.map(tab => `<button class="${active === tab ? "active" : ""}" aria-pressed="${active === tab}" data-mode="${tab}">${tab === "balance" ? "Твой баланс" : tab === "reasonable" ? "Разумный выбор" : "Выбор сердцем"}</button>`).join("")}</div>${cards.length ? `<div class="result-list">${cards.map(renderCarCard).join("")}</div>` : `<section class="empty"><h2>Нет совпадений</h2><p>Ограничения, исключившие больше всего моделей, — ${Object.entries(result.topConstraints || {}).slice(0, 3).map(([key, count]) => esc(requirements[key] || key) + " (" + count + ")").join(", ") || "проверьте ответы"}.</p><button class="primary" data-action="edit">Вернуться к вопросам</button></section>`}`);
}
function renderCarCard(candidate) { const car = candidate.car || carById(candidate.carId); const saved = state.garage.some(item => item.carId === car.id); const score = Math.round((candidate.scores?.final || 0) * 100); const reason = candidate.matched?.[0] || "соответствует части ваших критериев"; const tradeoff = candidate.tradeoffs?.[0]; return `<article class="car-card result-card"><div class="fit-badge"><strong>${score}%</strong><span>совпадение</span></div>${photo(car, "result-photo")}<div class="car-content"><div class="eyebrow">#${candidate.rank || ""} · ${esc(car.brand)}</div><h2>${esc(car.model)} ${esc(car.generation || "")}</h2><p class="card-pitch">${esc(reason)}</p><p class="muted">${esc(car.modification || "")} · ${car.facts?.price ? "ориентир " + money(car.facts.price.min) + "–" + money(car.facts.price.max) : "цена уточняется"}</p><div class="facts"><span>${car.facts?.seats || "?"} мест</span><span>${car.facts?.luggageLiters || "?"} л</span><span>${esc(car.facts?.transmission || "данные уточняются")}</span></div><details class="why"><summary>Почему подходит</summary><ul class="reason-list">${(candidate.matched || []).map(item => `<li class="match">${esc(item)}</li>`).join("")}${tradeoff ? `<li class="tradeoff"><b>Главный компромисс:</b> ${esc(tradeoff)}</li>` : ""}${(candidate.unknown || []).map(item => `<li class="unknown">${esc(item)}</li>`).join("")}</ul></details>${candidate.alternative ? `<p class="muted">Альтернатива <button class="ghost" data-car="${esc(candidate.alternative.id)}">${esc(candidate.alternative.brand)} ${esc(candidate.alternative.model)}</button></p>` : ""}<div class="card-actions"><button class="${saved ? "secondary" : "primary"}" data-save="${esc(car.id)}">${saved ? "В гараже" : "Сохранить в гараж"}</button><button class="ghost" data-car="${esc(car.id)}">Подробнее</button><button class="ghost" data-compare="${esc(car.id)}">Сравнить</button></div></div></article>`; }

function renderGarage() { return shell(`<section class="results-head"><div><div class="eyebrow">Личный гараж</div><h1>${state.garage.length ? `${state.garage.length} автомобиля` : "Гараж пока пуст"}</h1><p class="muted">Отметьте машины, чтобы поделиться ими по ссылке.</p></div><button class="secondary" data-action="share" ${state.garage.length ? "" : "disabled"}>Создать ссылку</button></section>${state.garage.length ? `<div class="garage-list">${state.garage.map(item => { const car = carById(item.carId); return car ? `<article class="garage-item">${photo(car, "garage-photo")}<div><div class="eyebrow">${esc(car.brand)}</div><h2>${esc(car.model)}</h2><p class="muted">${esc(car.modification || "")} · статус: ${esc(item.status || "интересно")}</p><label class="share-option"><input type="checkbox" data-share-car="${esc(item.carId)}"> Включить в ссылку</label><input class="note-input" aria-label="Личная заметка" maxlength="1000" data-note="${esc(item.carId)}" value="${esc(item.note || "")}" placeholder="Личная заметка"><select aria-label="Статус автомобиля" data-status="${esc(item.carId)}"><option ${item.status === "интересно" ? "selected" : ""}>интересно</option><option ${item.status === "рассматриваю" ? "selected" : ""}>рассматриваю</option><option ${item.status === "мечта" ? "selected" : ""}>мечта</option><option ${item.status === "владею" ? "selected" : ""}>владею</option></select></div><button class="ghost danger" data-remove="${esc(item.carId)}">Удалить</button></article>` : ""; }).join("")}</div>` : `<section class="empty"><p>Сохраните модели из результата подбора, чтобы сравнить их позже.</p><button class="primary" data-action="start">Начать подбор</button></section>`}${renderLinks()}`); }

function renderLinks() {
  if (!state.links.length) return "";
  return `<section class="panel links"><h2>Ссылки на гараж</h2>${state.links.map(link => `<p><a href="#share/${esc(link.token)}" target="_blank" rel="noopener">Открыть гараж по ссылке</a> <button class="ghost" data-revoke="${esc(link.token)}">Отозвать</button></p>`).join("")}</section>`;
}

function renderCompare() {
  const cars = state.compare.map(carById).filter(Boolean);
  if (cars.length < 2) return shell('<section class="empty"><h1>Недостаточно машин</h1><p>Выберите минимум две модели в гараже.</p><button class="primary" data-action="garage">В гараж</button></section>');
  const rows = [["Кузов", car => bodies[car.facts?.bodyType]], ["Места", car => car.facts?.seats], ["Багажник", car => car.facts?.luggageLiters ? `${car.facts.luggageLiters} л` : car.facts?.luggageClass], ["Привод", car => car.facts?.drive], ["Коробка", car => car.facts?.transmission], ["Силовая установка", car => car.facts?.powertrain], ["Клиренс", car => car.facts?.clearanceMm ? `${car.facts.clearanceMm} мм` : "нет данных"], ["Цена от", car => car.facts?.price ? money(car.facts.price.min) : "нет данных"]];
  return shell(`<button class="back-link" data-action="garage">← В гараж</button><section class="panel compare"><div class="eyebrow">Сравнение</div><h1>Что отличается</h1><div class="compare-table"><div class="compare-row compare-head"><strong>Параметр</strong>${cars.map(car => `<strong>${esc(car.brand)} ${esc(car.model)}</strong>`).join("")}</div>${rows.map(([label, getter]) => `<div class="compare-row"><span>${esc(label)}</span>${cars.map(car => `<strong>${esc(getter(car) || "нет данных")}</strong>`).join("")}</div>`).join("")}</div><p class="muted">Данные каталога требуют проверки по конкретной комплектации.</p></section>`);
}

function renderProfile() { return shell(`<section class="profile"><div class="eyebrow">Профиль</div><h1>${state.demo ? esc(state.demo.displayName) : "Гостевой профиль"}</h1><p class="muted">${state.demo ? "Демо-профиль с готовым подбором" : "Ответы и гараж доступны только в этом браузере"}</p><div class="profile-grid"><div class="panel"><h2>Сводка подбора</h2><p>${state.profile.useCases?.length ? `Сценарии: ${state.profile.useCases.map(key => labels[key] || key).join(", ")}` : "Сценарий ещё не выбран"}</p><p>${state.profile.passengers ? `Пассажиров: ${state.profile.passengers}` : "Пассажиры не указаны"}</p><p>${state.profile.budget?.status === "provided" ? `Бюджет: ${money(state.profile.budget.min)}–${money(state.profile.budget.max)}` : "Бюджет скрыт или неизвестен"}</p></div><div class="panel"><h2>Демо-режим</h2><p>Можно открыть готовый профиль без регистрации.</p>${state.demo ? `<div class="card-actions"><button class="primary" data-action="results">Открыть результат</button><button class="secondary" data-action="garage">Открыть гараж</button><button class="ghost" data-action="demo-reset">Сбросить демо</button><button class="ghost" data-action="demo-exit">Выйти из демо</button></div>` : '<button class="primary" data-action="demo-list">Открыть демо-профили</button>'}</div></div></section>`); }
function renderDemoList() { return shell(`<section class="profile"><div class="eyebrow">Демонстрация</div><h1>Готовые профили</h1><p class="muted">Каждый профиль показывает отдельный сценарий продукта.</p><div class="demo-grid"><button data-demo="first-car"><strong>Демо-первый автомобиль</strong><span>Городские модели и спокойный бюджет</span></button><button data-demo="family-travel"><strong>Демо-семья и путешествия</strong><span>Пять пассажиров, багаж и поездки</span></button><button data-demo="heart-choice"><strong>Демо-выбор сердцем</strong><span>Яркие и спортивные автомобили</span></button></div></section>`); }
function renderCar(id) { const car = carById(id); if (!car) return renderHome(); return shell(`<button class="back-link" data-action="results">← Назад к результатам</button><article class="detail">${photo(car, "detail-photo")}<div><div class="eyebrow">${esc(car.brand)} · ${esc(car.generation || "")}</div><h1>${esc(car.model)}</h1><p class="lead">${esc(car.modification || "")} · ${car.facts?.price ? "ориентир " + money(car.facts.price.min) + "–" + money(car.facts.price.max) : "цена уточняется"}</p>${car.description ? `<p>${esc(car.description)}</p>` : ""}<div class="spec-grid">${[["Кузов", bodies[car.facts?.bodyType]], ["Места", car.facts?.seats], ["Багажник", car.facts?.luggageLiters ? `${car.facts.luggageLiters} л` : car.facts?.luggageClass], ["Привод", car.facts?.drive], ["Коробка", car.facts?.transmission], ["Силовая установка", car.facts?.powertrain], ["Клиренс", car.facts?.clearanceMm ? `${car.facts.clearanceMm} мм` : "нет данных"]].map(([key, value]) => `<div><span>${esc(key)}</span><strong>${esc(value || "нет данных")}</strong></div>`).join("")}</div><p class="muted">Характеристики требуют проверки по конкретной комплектации. Стилевые теги — редакционная оценка.</p><button class="primary" data-save="${esc(car.id)}">Сохранить в гараж</button></div></article>`); }

// Application event handlers
function renderShare() {
  const shared = state.shared;
  if (!shared) return shell('<section class="empty"><h1>Загружаем гараж</h1></section>');
  if (shared.error) return shell('<section class="empty"><h1>Ссылка недоступна</h1><button class="secondary" data-action="home">На главную</button></section>');
  const entries = shared.items.map(item => {
    const car = carById(item.carId);
    if (!car) return "";
    return `<article class="garage-item">${photo(car, "garage-photo")}<div><h2>${esc(car.brand)} ${esc(car.model)}</h2><p>${esc(item.status)}</p></div><button class="secondary" data-car="${esc(car.id)}">Подробнее</button></article>`;
  });
  return shell(`<h1>Гараж по ссылке</h1><div class="garage-list">${entries.join("")}</div>`);
}

function render() {
  const route = getRoute();
  const pages = { home: renderHome, test: renderTest, duels: renderDuels, results: renderResults, garage: renderGarage, compare: renderCompare, profile: renderProfile, "demo-list": renderDemoList };
  let content;
  if (!state.catalog.length) {
    content = shell('<section class="empty"><h1>Загружаем каталог</h1><button class="secondary" data-action="reload">Повторить загрузку</button></section>');
  } else if (route.startsWith("share/")) {
    const token = route.slice(6);
    if (state.shared?.token !== token) {
      state.shared = null;
      loadShare(token);
    }
    content = renderShare();
  } else if (route.startsWith("car/")) {
    content = renderCar(route.slice(4));
  } else {
    content = Object.hasOwn(pages, route) ? pages[route]() : renderHome();
  }
  document.getElementById("app").innerHTML = content + (errorMessage ? `<p class="notice error" role="alert">${esc(errorMessage)}</p>` : "");
  observePhotos(document.getElementById("app"));
}

async function loadShare(token) {
  try {
    const data = await api("/api/share/" + encodeURIComponent(token));
    if (getRoute() === "share/" + token) state.shared = { token, ...data };
  } catch {
    if (getRoute() === "share/" + token) state.shared = { token, error: true };
  }
  if (getRoute() === "share/" + token) render();
}

async function perform(operation, control) {
  if (busy) return;
  busy = true;
  errorMessage = "";
  if (control) control.disabled = true;
  try {
    await operation();
  } catch (error) {
    errorMessage = error instanceof Error && error.message !== "Failed to fetch" ? error.message : "Сервис временно недоступен";
    const existing = document.querySelector(".notice.error");
    existing?.remove();
    const notice = document.createElement("p");
    notice.className = "notice error";
    notice.setAttribute("role", "alert");
    notice.textContent = errorMessage;
    document.getElementById("app").append(notice);
  } finally {
    if (control) control.disabled = false;
    busy = false;
  }
}

function start(profile = defaultProfile(), plan = null) {
  state.interview = plan;
  profile.answerStatuses ??= {};
  state.profile = profile;
  state.result = null;
  state.testStep = 0;
  state.duel = null;
  navigate("test");
}

async function advance(skip = false) {
  const question = activeQuestions()[state.testStep];
  if (!question) return;
  if (skip) {
    state.profile[question.key] = defaultProfile()[question.key];
    if (question.key === "budget") state.profile.budget.status = "skipped";
    state.profile.answerStatuses[question.key] = "skipped";
  } else if (question.type === "budget") {
    const min = readBudget("budgetMin");
    const max = readBudget("budgetMax");
    if (min !== null && max !== null && min > max) throw new Error("Верхняя граница бюджета должна быть не меньше нижней");
    state.profile.budget = { min, max, status: min !== null || max !== null ? "provided" : "unknown" };
    state.profile.answerStatuses.budget = state.profile.budget.status;
  }
  state.testStep++;
  const plan = state.interview;
  if (plan && !plan.refreshed && state.testStep === 3) {
    plan.refreshed = true;
    const completed = plan.order.slice(0, state.testStep);
    const answered = completed.map(item => item.key);
    try {
      const { questions: updates } = await post("/api/ai/questions", { text: state.profile.sourceText, answered, answers: state.profile });
      if (updates.length) plan.order = orderQuestions(updates, completed);
    } catch {
      // The original plan remains available when the provider is unreachable.
    }
  }
  persist();
  render();
}

function readBudget(id) {
  const input = document.getElementById(id);
  if (!input?.value) return null;
  const value = Number(input.value);
  if (!Number.isSafeInteger(value) || value < 1) throw new Error("Укажите бюджет целым числом больше нуля");
  return value;
}

async function runDuels(choice) {
  const request = { profile: state.profile };
  if (choice) {
    request.choice = choice;
    request.pair = [state.duel.left.id, state.duel.right.id];
  }
  const { profile, duel } = await post("/api/duels", request);
  state.profile = profile;
  state.duel = duel;
  persist();
  if (duel) navigate("duels");
  else {
    navigate("test");
    await calculate();
  }
}

async function openDemo(demoKey) {
  const demo = await post("/api/auth/demo", { demoKey });
  state.interview = null;
  state.demo = { displayName: demo.displayName, demoKey, garage: demo.garage };
  state.profile = demo.profile;
  state.result = demo.recommendation;
  state.garage = demo.garage;
  state.profile.answerStatuses ??= {};
  state.duel = null;
  state.testStep = 0;
  navigate("profile");
}

if (state.demo?.garage) state.garage = state.demo.garage;

const actions = {
  home: () => navigate("home"),
  start: () => {
    const description = document.getElementById("freeText");
    if (description?.value.trim()) return actions["start-text"]();
    if (!description) navigate("home");
    document.getElementById("freeText")?.focus();
  },
  unknown: () => start(),
  "start-text": async () => {
    const text = document.getElementById("freeText").value.trim();
    const button = document.querySelector('[data-action="start-text"]');
    const label = button.textContent;
    button.textContent = "Готовим вопросы…";
    try {
      const { profile, summary, questions: proposals, provider, aiStatus } = await post("/api/ai/parse-profile", { text });
      start(profile, { summary, provider, aiStatus, order: orderQuestions(proposals), refreshed: false });
    } finally {
      button.textContent = label;
    }
  },
  next: () => advance(),
  skip: () => advance(true),
  back: () => { state.testStep = Math.max(0, state.testStep - 1); persist(); render(); },
  "budget-unknown": () => {
    document.getElementById("budgetMin").value = "";
    document.getElementById("budgetMax").value = "";
    return advance();
  },
  "skip-style": () => {
    state.profile.style = defaultProfile().style;
    state.profile.answerStatuses.style = "skipped";
    return runDuels();
  },
  duels: () => runDuels(),
  finish: () => calculate(),
  edit: () => { state.testStep = 0; state.profile.duelHistory = []; state.duel = null; navigate("test"); },
  results: () => navigate("results"),
  garage: () => navigate("garage"),
  compare: () => navigate("compare"),
  profile: () => navigate("profile"),
  "demo-list": () => navigate("demo-list"),
  "demo-reset": () => openDemo(state.demo.demoKey),
  "demo-exit": () => {
    state.demo = null;
    state.garage = readStorage(GARAGE_KEY, []);
    start();
  },
  share: async () => {
    const selected = [...document.querySelectorAll("[data-share-car]:checked")].map(input => input.dataset.shareCar);
    if (!selected.length) throw new Error("Отметьте автомобили, которыми хотите поделиться");
    const items = state.garage.filter(item => selected.includes(item.carId)).map(({ carId, status }) => ({ carId, status }));
    const link = await post("/api/share", { items });
    state.links.push(link);
    persist();
    render();
  },
  reload: async () => { await loadCatalog(); render(); },
};

document.getElementById("app").addEventListener("click", event => {
  const button = event.target.closest("button");
  if (!button || button.type === "submit" && button.form?.id === "description-form") return;
  const data = button.dataset;
  perform(async () => {
    if (data.action && Object.hasOwn(actions, data.action)) return actions[data.action]();
    if (data.duel && state.duel) return runDuels(data.duel);
    if (data.mode && data.mode !== state.result?.mode) return calculate(data.mode);
    if (data.car) return navigate("car/" + data.car);
    if (data.compare) {
      state.compare = state.compare.includes(data.compare) ? state.compare.filter(id => id !== data.compare) : [...state.compare, data.compare].slice(-4);
      persist();
      if (state.compare.length >= 2) navigate("compare");
      else render();
      return;
    }
    if (data.compare) {
      state.compare = state.compare.includes(data.compare) ? state.compare.filter(id => id !== data.compare) : [...state.compare, data.compare].slice(-4);
      persist();
      render();
      return;
    }
    if (data.demo) return openDemo(data.demo);
    if (data.choice) {
      const question = questions.find(item => item.key === data.choice);
      const value = question.options.find(option => String(option[0]) === data.value)[0];
      if (question.type === "multi") {
        const current = state.profile[data.choice];
        state.profile[data.choice] = current.includes(value) ? current.filter(item => item !== value) : [...current, value];
      } else if (question.type === "priority") {
        state.profile.priorities ??= {};
        state.profile.priorities[value] = state.profile.priorities[value] == null ? 0.9 : null;
      } else state.profile[data.choice] = value;
      state.profile.answerStatuses[data.choice] = "provided";
    }
    if (data.quick) {
      const profile = defaultProfile();
      if (data.quick === "heart") {
        Object.assign(profile.style, { brightness: 0.9, sportiness: 0.85, status: 0.75 });
        profile.answerStatuses.style = "provided";
      } else {
        profile.useCases = [data.quick];
        profile.answerStatuses.useCases = "provided";
      }
      return start(profile);
    }
    if (data.save && carById(data.save) && !state.garage.some(item => item.carId === data.save)) {
      state.garage.push({ carId: data.save, status: "интересно", note: "" });
    }
    if (data.remove) {
      const index = state.garage.findIndex(item => item.carId === data.remove);
      if (index !== -1) state.garage.splice(index, 1);
    }
    if (data.revoke) {
      const link = state.links.find(item => item.token === data.revoke);
      await api("/api/share/" + encodeURIComponent(link.token), { method: "DELETE", headers: { "X-Revoke-Key": link.revokeKey } });
      state.links = state.links.filter(item => item !== link);
    }
    persist();
    render();
  }, button);
});

document.getElementById("app").addEventListener("submit", event => {
  if (event.target.id !== "description-form") return;
  event.preventDefault();
  perform(actions["start-text"], event.submitter);
});

document.getElementById("app").addEventListener("input", event => {
  const input = event.target;
  if (input.dataset.style) {
    state.profile.style[input.dataset.style] = Number(input.value);
    state.profile.answerStatuses.style = "provided";
  } else if (input.id === "freeText") state.profile.sourceText = input.value;
  else if (input.dataset.note) {
    const item = state.garage.find(item => item.carId === input.dataset.note);
    if (item) item.note = input.value;
  } else return;
  persist();
});

document.getElementById("app").addEventListener("change", event => {
  if (!event.target.dataset.status) return;
  const item = state.garage.find(entry => entry.carId === event.target.dataset.status);
  if (item) item.status = event.target.value;
  persist();
  render();
});

window.addEventListener("hashchange", () => {
  if (!getRoute().startsWith("share/")) state.shared = null;
  errorMessage = "";
  render();
});
render();
perform(actions.reload);
