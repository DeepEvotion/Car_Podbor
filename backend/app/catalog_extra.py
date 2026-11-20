"""Additional editorial catalogue entries.

The values are representative ranges for the named generation, not a promise
about every trim. Sources are included in each record so the recommender can
explain what is known and what must be checked for a particular car.
"""

ROWS = [
    ("toyota-corolla-xii", "Toyota", "Corolla", "XII", "1.6 CVT", "sedan", 5, 471, "medium", "front", "cvt", "petrol", 150, 2100000, 3100000, .55, .65, .62, .35, .70, .65, .65, "Практичный седан для города и трассы с хорошей ликвидностью."),
    ("kia-rio-iv", "Kia", "Rio", "IV", "1.6 AT", "sedan", 5, 480, "large", "front", "automatic", "petrol", 160, 1300000, 2100000, .45, .55, .58, .30, .72, .42, .70, "Компактный и понятный автомобиль для города."),
    ("volkswagen-polo-vi", "Volkswagen", "Polo", "VI", "1.6 AT", "sedan", 5, 460, "large", "front", "automatic", "petrol", 170, 1400000, 2300000, .42, .58, .62, .32, .70, .50, .72, "Сдержанный седан с удобной посадкой и умеренными расходами."),
    ("skoda-rapid-ii", "Skoda", "Rapid", "II", "1.4 TSI DSG", "hatchback", 5, 530, "large", "front", "robot", "petrol", 170, 1700000, 2700000, .40, .65, .68, .35, .82, .48, .68, "Практичный лифтбек с большим багажником."),
    ("renault-logan-ii", "Renault", "Logan", "II", "1.6 AT", "sedan", 5, 510, "large", "front", "automatic", "petrol", 172, 1100000, 1800000, .32, .30, .48, .20, .80, .20, .68, "Простой просторный седан с недорогим обслуживанием."),
    ("lada-vesta-ng", "Lada", "Vesta", "NG", "1.6 CVT", "sedan", 5, 480, "large", "front", "cvt", "petrol", 178, 1500000, 2400000, .48, .52, .60, .34, .75, .28, .62, "Отечественный седан для города, семьи и плохих дорог."),
    ("honda-civic-x", "Honda", "Civic", "X", "1.5 CVT", "sedan", 5, 428, "medium", "front", "cvt", "petrol", 135, 2200000, 3500000, .55, .75, .62, .55, .62, .60, .65, "Драйверский городской седан с экономичным турбомотором."),
    ("toyota-camry-viii", "Toyota", "Camry", "VIII", "2.5 AT", "sedan", 5, 493, "medium", "front", "automatic", "petrol", 155, 3300000, 5200000, .48, .70, .82, .38, .65, .82, .42, "Комфортный седан для дальних поездок и статуса."),
    ("mazda-6-iii", "Mazda", "6", "III", "2.5 AT", "sedan", 5, 429, "medium", "front", "automatic", "petrol", 165, 2700000, 4300000, .62, .72, .70, .72, .62, .65, .48, "Элегантный седан с приятным управлением."),
    ("bmw-3-series-g20", "BMW", "3 Series", "G20", "320i AT", "sedan", 5, 480, "large", "rear", "automatic", "petrol", 145, 4500000, 7500000, .65, .88, .62, .85, .45, .82, .55, "Спортивный премиальный седан для водителя."),
    ("mercedes-c-class-w206", "Mercedes-Benz", "C-Class", "W206", "C180 AT", "sedan", 5, 455, "medium", "rear", "automatic", "hybrid", 130, 5200000, 8500000, .58, .92, .82, .62, .48, .92, .52, "Технологичный и комфортный премиальный седан."),
    ("audi-a4-b9", "Audi", "A4", "B9", "40 TFSI S tronic", "sedan", 5, 460, "medium", "front", "robot", "petrol", 145, 3800000, 6500000, .48, .82, .72, .60, .60, .78, .56, "Сбалансированный седан с качественным салоном."),
    ("volvo-s60-iii", "Volvo", "S60", "III", "B4 AT", "sedan", 5, 442, "medium", "front", "automatic", "hybrid", 142, 3800000, 6500000, .46, .78, .82, .48, .62, .82, .55, "Безопасный и спокойный премиальный седан."),
    ("ford-mondeo-v", "Ford", "Mondeo", "V", "2.0 AT", "sedan", 5, 550, "large", "front", "automatic", "petrol", 145, 1800000, 3000000, .42, .60, .72, .42, .78, .40, .40, "Просторный автомобиль для трассы и семьи."),
    ("honda-jazz-iv", "Honda", "Jazz", "IV", "e:HEV", "hatchback", 5, 304, "medium", "front", "automatic", "hybrid", 136, 1900000, 3200000, .65, .80, .62, .30, .70, .48, .90, "Манёвренный экономичный городской хэтчбек."),
    ("toyota-yaris-iv", "Toyota", "Yaris", "IV", "1.5 Hybrid", "hatchback", 5, 286, "medium", "front", "automatic", "hybrid", 135, 1800000, 3000000, .62, .82, .60, .30, .68, .48, .92, "Компактный гибрид для плотного города."),
    ("renault-captur-ii", "Renault", "Captur", "II", "1.3 CVT", "crossover", 5, 422, "medium", "front", "cvt", "petrol", 174, 2100000, 3500000, .55, .68, .68, .42, .78, .38, .62, "Городской кроссовер с удобной посадкой."),
    ("hyundai-creta-ii", "Hyundai", "Creta", "II", "2.0 AT AWD", "crossover", 5, 433, "medium", "awd", "automatic", "petrol", 190, 2300000, 3900000, .58, .72, .70, .45, .80, .52, .50, "Универсальный кроссовер для города и поездок."),
    ("kia-seltos-i", "Kia", "Seltos", "I", "2.0 CVT AWD", "crossover", 5, 433, "medium", "awd", "cvt", "petrol", 190, 2300000, 3900000, .58, .75, .68, .52, .76, .48, .52, "Компактный современный кроссовер с хорошей оснащённостью."),
    ("toyota-corolla-cross-i", "Toyota", "Corolla Cross", "I", "2.0 Hybrid", "crossover", 5, 436, "medium", "front", "automatic", "hybrid", 161, 3000000, 4800000, .55, .82, .74, .40, .74, .70, .52, "Экономичный семейный кроссовер."),
    ("volkswagen-t-roc-i", "Volkswagen", "T-Roc", "I", "1.5 DSG", "crossover", 5, 445, "medium", "front", "robot", "petrol", 161, 2500000, 4300000, .58, .75, .68, .52, .68, .58, .55, "Европейский кроссовер с компактными габаритами."),
    ("nissan-qashqai-iii", "Nissan", "Qashqai", "III", "1.3 CVT", "crossover", 5, 504, "large", "front", "cvt", "petrol", 200, 2700000, 4500000, .50, .75, .76, .42, .82, .55, .45, "Комфортный семейный кроссовер с большим багажником."),
    ("mazda-cx30-i", "Mazda", "CX-30", "I", "2.0 AT AWD", "crossover", 5, 430, "medium", "awd", "automatic", "petrol", 175, 2800000, 4500000, .62, .80, .72, .70, .64, .62, .58, "Стильный компактный кроссовер с точным рулём."),
    ("subaru-forester-v", "Subaru", "Forester", "V", "2.5 CVT AWD", "suv", 5, 509, "large", "awd", "cvt", "petrol", 220, 3500000, 5700000, .45, .62, .82, .42, .86, .55, .35, "Практичный безопасный автомобиль для путешествий и плохих дорог."),
    ("mitsubishi-outlander-iv", "Mitsubishi", "Outlander", "IV", "2.5 CVT AWD", "suv", 7, 478, "large", "awd", "cvt", "petrol", 213, 3500000, 6000000, .45, .70, .82, .40, .90, .55, .25, "Большой семейный кроссовер с семью местами."),
    ("nissan-x-trail-iv", "Nissan", "X-Trail", "IV", "1.5 e-Power", "suv", 5, 575, "large", "awd", "automatic", "hybrid", 205, 3600000, 6000000, .48, .78, .84, .40, .90, .58, .28, "Просторный семейный кроссовер для дальних поездок."),
    ("skoda-kodiaq-i", "Skoda", "Kodiaq", "I", "2.0 TSI DSG", "suv", 7, 835, "large", "awd", "robot", "petrol", 194, 3500000, 6000000, .42, .70, .84, .38, .94, .60, .20, "Практичный семиместный автомобиль с огромным багажником."),
    ("volkswagen-touareg-iii", "Volkswagen", "Touareg", "III", "3.0 TDI AT AWD", "suv", 5, 810, "large", "awd", "automatic", "diesel", 200, 5500000, 9500000, .42, .78, .90, .48, .86, .82, .18, "Комфортный большой SUV для трассы и путешествий."),
    ("bmw-x3-g01", "BMW", "X3", "G01", "30i AT AWD", "crossover", 5, 550, "large", "awd", "automatic", "petrol", 204, 5200000, 8500000, .55, .86, .78, .78, .72, .82, .36, "Премиальный кроссовер с азартным управлением."),
    ("mercedes-glc-x254", "Mercedes-Benz", "GLC", "X254", "300 4MATIC", "crossover", 5, 620, "large", "awd", "automatic", "hybrid", 200, 6500000, 10500000, .50, .94, .88, .62, .78, .95, .32, "Тихий премиальный кроссовер с высоким комфортом."),
    ("audi-q5-ii", "Audi", "Q5", "II", "45 TFSI quattro", "crossover", 5, 520, "large", "awd", "robot", "petrol", 200, 5000000, 8500000, .45, .84, .80, .58, .76, .84, .34, "Технологичный универсальный кроссовер."),
    ("lexus-rx-v", "Lexus", "RX", "V", "350h AWD", "suv", 5, 612, "large", "awd", "automatic", "hybrid", 205, 6000000, 10000000, .48, .88, .92, .46, .82, .94, .28, "Тихий надёжный кроссовер для комфорта и статуса."),
    ("toyota-land-cruiser-300", "Toyota", "Land Cruiser", "300", "3.5 AT AWD", "suv", 7, 1131, "large", "awd", "automatic", "petrol", 235, 9000000, 15000000, .35, .72, .90, .48, .92, .98, .10, "Большой выносливый внедорожник для путешествий и тяжёлых дорог."),
    ("ford-ranger-iv", "Ford", "Ranger", "IV", "2.0 AT 4WD", "suv", 5, 1200, "large", "awd", "automatic", "diesel", 237, 4000000, 7000000, .38, .62, .64, .65, .96, .58, .12, "Пикап для работы, дачи и бездорожья."),
    ("hyundai-santa-fe-v", "Hyundai", "Santa Fe", "V", "2.5 AT AWD", "suv", 7, 634, "large", "awd", "automatic", "petrol", 177, 4500000, 7500000, .52, .82, .86, .45, .90, .68, .20, "Большой современный семейный кроссовер."),
    ("kia-sorento-iv", "Kia", "Sorento", "IV", "2.2 AT AWD", "suv", 7, 616, "large", "awd", "automatic", "diesel", 185, 4000000, 7000000, .48, .76, .84, .42, .92, .62, .22, "Семиместный автомобиль для семьи и путешествий."),
    ("toyota-prius-v", "Toyota", "Prius", "V", "1.8 Hybrid", "hatchback", 5, 446, "large", "front", "automatic", "hybrid", 136, 2200000, 3800000, .55, .80, .68, .25, .74, .58, .75, "Экономичный гибрид с низким расходом топлива."),
    ("hyundai-ioniq-5-i", "Hyundai", "Ioniq 5", "I", "Long Range AWD", "crossover", 5, 527, "large", "awd", "automatic", "electric", 160, 4500000, 7500000, .72, 1.0, .78, .62, .72, .78, .45, "Просторный электромобиль с быстрой зарядкой."),
    ("volkswagen-id4-i", "Volkswagen", "ID.4", "I", "Pro Performance", "crossover", 5, 543, "large", "rear", "automatic", "electric", 163, 4000000, 6800000, .52, .92, .78, .38, .78, .62, .40, "Спокойный электрический кроссовер для города и трассы."),
    ("bmw-ix1-u11", "BMW", "iX1", "U11", "xDrive30", "crossover", 5, 490, "large", "awd", "automatic", "electric", 170, 5500000, 9000000, .55, 1.0, .78, .72, .68, .82, .42, "Динамичный премиальный электрокроссовер."),
]


def build_catalog():
    result = []
    for row in ROWS:
        (id_, brand, model, generation, modification, body, seats, luggage, luggage_class, drive, transmission, powertrain, clearance, pmin, pmax,
         brightness, modernity, comfort, sportiness, practicality, status, compactness, description) = row
        style = {"brightness": brightness, "modernity": modernity, "comfort": comfort, "sportiness": sportiness, "practicality": practicality, "status": status, "compactness": compactness, "technology": modernity, "retro": max(0, 1 - modernity)}
        result.append({"id": id_, "brand": brand, "model": model, "generation": generation, "modification": modification, "description": description,
            "facts": {"bodyType": body, "seats": seats, "luggageLiters": luggage, "luggageClass": luggage_class, "drive": drive, "transmission": transmission, "powertrain": powertrain, "clearanceMm": clearance, "price": {"min": pmin, "max": pmax, "currency": "RUB"}},
            "style": style, "suitability": {"city": .8 if body in ("hatchback", "sedan") else .65, "highway": .8, "travel": .8, "poorRoads": min(1, clearance / 230), "family": .9 if seats >= 5 else .35, "work": .65},
            "dataQuality": {"facts": "editorial_range", "style": "editorial", "sources": ["https://www.media.volvocars.com/", "https://www.euroncap.com/"], "verification": "check_trim"}})
    return result[:36]
