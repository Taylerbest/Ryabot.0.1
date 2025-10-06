# config/texts.py
"""
Все тексты для бота - ФИНАЛЬНЫЕ НАЗВАНИЯ КНОПОК
ВНИМАНИЕ: Названия кнопок НЕЛЬЗЯ менять! Они установлены пользователем!
"""

# === ОСНОВНЫЕ КНОПКИ МЕНЮ ===

# Главное меню острова (нижние кнопки)
BTN_FARM = "🏡 Ферма"
BTN_TOWN = "🏢 Город" 
BTN_CITIZEN = "👤 Житель"
BTN_WORK = "💼 Рябота"
BTN_INVENTORY = "🎒 Рюкзак"
BTN_FRIENDS = "👥 Друзья"
BTN_LEADERBOARD = "🏆 Лидеры"
BTN_OTHER = "🗄 Прочее"

# Статистические кнопки (верхний инлайн ряд)
BTN_STATS_RBTC = "👉📊💠"
BTN_STATS_FARM = "📊🏡"
BTN_STATS_CITY = "📊🏢" 
BTN_STATS_WORK = "📊💼"

# === КНОПКИ ГОРОДА ===
BTN_TOWNHALL = "🏛 Ратуша"
BTN_MARKET = "🛒 Рынок"
BTN_RYABANK = "🏦 Рябанк"
BTN_SHOP = "🏪 Магазин"
BTN_PAWNSHOP = "💍 Ломбард"
BTN_TAVERN = "🍻 Таверна"
BTN_ACADEMY = "🏫 Академия"
BTN_FORTUNE = "🎡 Фортуна"
BTN_REALESTATE = "🏞 Недвижка"
BTN_VETCENTER = "❤️‍🩹 Ветцентр"
BTN_CONSTRUCTION = "🏗 Стройсам"
BTN_HOSPITAL = "🏥 Больница"
BTN_QUANTUMHUB = "⚛️ Квантхаб"
BTN_CEMETERY = "🪦 Кладбище"

# === КНОПКИ РАБОТ ===
BTN_WORK_BREACH = "⚠️ Брешь"
BTN_WORK_EXPEDITION = "🏕 Вылазка"
BTN_WORK_CITY = "🏢 Город"
BTN_WORK_FARM = "🏡 Ферма"
BTN_WORK_FOREST = "🌲 Лес"
BTN_WORK_SEA = "🌊 Море"

# === КНОПКИ ЖИТЕЛЯ ===
BTN_CITIZEN_PROPERTIES = "🏞 Владения"
BTN_CITIZEN_WARDROBE = "🥼 Гардероб"
BTN_CITIZEN_HISTORY = "📖 История"
BTN_CITIZEN_TASKS = "📝 Задачи"
BTN_CITIZEN_ACHIEVEMENTS = "🎯 Достижения"
BTN_CITIZEN_STATISTICS = "📊 Статистика"

# === КНОПКИ ФЕРМЫ ===
BTN_FARM_HENHOUSE = "🐔 Курятник"
BTN_FARM_COWSHED = "🐄 Коровник"
BTN_FARM_SHEEPFOLD = "🐑 Овчарня"
BTN_FARM_PIGSTY = "🐖 Свинарник"
BTN_FARM_APIARY = "🐝 Пасека"
BTN_FARM_GARDEN = "🪴 Огород"
BTN_FARM_FORESTRY = "🌳 Лесхоз"
BTN_FARM_FISHPOND = "🌊 Рыбник"
BTN_FARM_MINE = "🪨 Рудник"
BTN_FARM_VILLAGE = "🏘 Деревня"
BTN_FARM_QUANTUMLAB = "⚛️ КвантЛаб"
BTN_FARM_STABLE = "🐎 Конюшня"

# === КНОПКИ РЮКЗАКА ===
BTN_INVENTORY_WALLET = "👉💰 Кошелек"
BTN_INVENTORY_PASSES = "🎫 Допуски"
BTN_INVENTORY_PRODUCTS = "🥚 Продукты"
BTN_INVENTORY_HARVEST = "🥕 Урожай"
BTN_INVENTORY_ANIMALS = "🐮 Животные"
BTN_INVENTORY_SEEDS = "🍃 Семена"
BTN_INVENTORY_RESOURCES = "🪵 Ресурсы"
BTN_INVENTORY_BOXES = "📦 Коробки"

# === КНОПКИ ЛИДЕРБОРДА ===
BTN_LEADERS_FARM = "🏡 Top 50"
BTN_LEADERS_WORK = "💼 Top 50"
BTN_LEADERS_TRADE = "⚖️ Top 50"
BTN_LEADERS_EXPEDITION = "🏕 Top 50"
BTN_LEADERS_GAMBLING = "🎲 Top 50"
BTN_LEADERS_FIGHT = "🥊 Top 50"
BTN_LEADERS_RACING = "🏇 Top 50"
BTN_LEADERS_RBTC = "💠 Top 50"
BTN_LEADERS_PARTNER = "🤝 Top 50"

# === КНОПКИ ДРУЗЕЙ ===
BTN_FRIENDS_MY = "👥 Мои Друзья"
BTN_FRIENDS_STORAGE = "🪙 Хранилище"
BTN_FRIENDS_SHOP = "🎟 Магазин"

# === КНОПКИ ПРОЧЕГО ===
BTN_OTHER_CHAT = "💬 Чат"
BTN_OTHER_WIKI = "🔮 Вики"
BTN_OTHER_HISTORY = "📖 История"
BTN_OTHER_DESIGN = "🎨 Дизайн"

# === УНИВЕРСАЛЬНЫЕ ===
BTN_BACK = "↩️ Назад"
BTN_CONTINUE = "➡️ Продолжить"

# ==========================================
# ТЕКСТЫ МЕНЮ - ТОЧНО КАК УКАЗАЛ ПОЛЬЗОВАТЕЛЬ
# ==========================================

# === ГЛАВНОЕ МЕНЮ ОСТРОВА ===
ISLAND_MAIN_MENU = """
💠 Добыто: {total_rbtc_mined} (сколько всего RBTC добыто игроками)
├⚛️ КвантЛаб: {quantum_labs}
├👥 Друзья: {friends_total}
├🏕 Вылазки: {expeditions_total}
├⚠️ Аномалии: {anomalies_total}
├🥊 Петуш. Бои: {fights_total}
├🏇 Скачки: {races_total}
└📦 Ящики: {boxes_total}
"""

# === МЕНЮ ГОРОДА ===
TOWN_MENU = """
🏢 ГОРОД ℹ️ [🔋{energy}]

«Жужжащий улей коммерции и хаоса! Воздух наполнен болтовнёй торговцев, расхваливающих свои товары, банкиров, пересчитывающих золотые яйца, и строителей, таскающих свежую древесину. В каждом переулке есть возможности — если знать, где искать».
"""

# === МЕНЮ РАБОТ ===
WORK_MENU = """
〰️〰️ 💼 РЯБОТА ℹ️ [🔋{energy}] 〰️〰️

📋 КОМАНДА (здесь сколько всего работников)
├🙍‍♂️ Рабочий: {workers_total}
├👷 Строитель: {builders_total}
├👩‍🌾 Фермер: {farmers_total}
├👨‍🚒 Лесник: {foresters_total}
├🎣 Рыбак: {fishermen_total}
├🧑‍🍳 Повар: {cooks_total}
├🧑‍⚕️ Доктор: {doctors_total}
├🧑‍🔬 Ученый: {scientists_total}
├🧑‍🏫 Учитель: {teachers_total}
├💂 Q-Солдат: {q_soldiers_total}

📊 Выполнено работ: {works_completed}
〰️〰️〰️〰️
💠 Пул Аномалий: {anomaly_pool}
💠 Пул Экспедиций: {expedition_pool}
🌟[💼] Рейтинг: {work_rating}
"""

# === МЕНЮ ЖИТЕЛЯ ===
CITIZEN_MENU = """
〰️ 👤 CITIZEN ID ℹ️ 〰️
├─ Имя: @{username}
└─ Регистрация: {registration_date}

🏆 РАНГИ 🏆
├🏡 Фермер: [{farmer_rank}]
├💼 Работодатель: [{employer_rank}]
├⚖️ Торговец: [{trader_rank}]
├💠 Сжигатель: [{burner_rank}]
├🏕 Исследователь: [{explorer_rank}]
├🎲 Азартник: [{gambler_rank}]
├🏇 Гонщик: [{racer_rank}]
├🥊 Боец: [{fighter_rank}]
└🤝 Партнер: [{partner_rank}]

🧪 Жидкий Опыт: {liquid_experience}
🧿 Q-Очки: {q_points}
"""

# === МЕНЮ ФЕРМЫ ===
FARM_MENU = """
〰️〰️ 🏡 ФЕРМА ℹ 〰️〰️

#️⃣ ID Фермера: #{farmer_id}
🖼 Площадь: {total_area} Га
〰️〰️〰️〰️
💠 Пул Лабораторий: {lab_pool}
🌟 Рейтинг Фермера: {farmer_rating}
"""

# === МЕНЮ РЮКЗАКА ===
INVENTORY_MENU = """
〰️💰 КОШЕЛЕК💰〰️

💵 Рябаксы: {ryabucks}
💠 RBTC: {rbtc}

〰️ 🎒 STORAGE ℹ️ 〰️
{storage_percent}% ({storage_used:,}/{storage_total:,})
"""

# Допуски
INVENTORY_PASSES = """
🎒ДОПУСКИ
├🎫[🏕]: {expedition_passes}
├🎫[⚠️]: {anomaly_passes}
├🎫[🏡]: {farm_passes}
├🎫[🏢]: {city_passes}
├🎫[🌲]: {forest_passes}
├🎫[🌊]: {sea_passes}
├🎫[🥊]: {fight_passes}
└📦[🏇]: {race_passes}
"""

# Продукты
INVENTORY_PRODUCTS = """
🎒ПРОДУКТЫ
├🥚 Яйцо: {eggs}
├🥛 Молоко: {milk}
├🍯 Мед: {honey}
├ 🐟 Рыба: {fish}
├🍗[🐔] Курятина: {chicken_meat}
├🍗[🐥] Цыпленок: {chick_meat}
├🥓 Свинина: {pork}
├🥩 Говядина: {beef}
├🥩 Телятина: {veal}
├🍖 Баранина: {mutton}
├🍖 Конина: {horse_meat}
└🍖 Дичь: {game_meat}
"""

# Урожай
INVENTORY_HARVEST = """
🎒УРОЖАЙ
├🌾 Зерно: {grain}
├🍅 Помидоры: {tomatoes}
├🥒 Огурцы: {cucumbers}
├🥔 Картофель: {potatoes}
├🥕 Морковь: {carrots}
└🍇 Виноград: {grapes}
"""

# Животные  
INVENTORY_ANIMALS = """
🎒ЖИВОТНЫЕ
├🐔 Ряба: {chickens}
├🐓 Петух: {roosters}
├🐥 Цыпленок: {chicks}
├🐄 Корова: {cows}
├🐂 Бык: {bulls}
├🐮 Теленок: {calves}
├🐖 Свинья: {pigs}
├🐷 Поросенок: {piglets}
├🐑 Овца: {sheep}
├🐑 Ягненок: {lambs}
├🐝 Пчела: {bees}
├🐎 Лошадь: {horses}
└🐴 Жеребенок: {foals}
"""

# Семена
INVENTORY_SEEDS = """
🎒СЕМЕНА
├🌱[🌳] Саженцы: {saplings}
├🍃[🌾] Зерно: {grain_seeds}
├🍃[🍅] Помидоры: {tomato_seeds}
├🍃[🥒] Огурцы: {cucumber_seeds}
├🍃[🥔] Картофель: {potato_seeds}
├🍃[🥕] Морковь: {carrot_seeds}
└🍃[🍇] Виноград: {grape_seeds}
"""

# Ресурсы
INVENTORY_RESOURCES = """
🎒РЕСУРСЫ
├⚜️ Золотое Яйцо: {golden_eggs}
├💫 Золотые Осколки: {golden_shards}
├🪶 Перо: {feathers}
├🕯 Пчелиный Воск: {beeswax}
├🧶 Конский Волос: {horse_hair}
├🧶 Овечья Шерсть: {sheep_wool}
├🪥 Щетина: {bristles}
├🟫 Кожа: {leather}
├🦴 Кости: {bones}
├💩 Навоз: {manure}
├🪨 Камень: {stone}
└🪵 Древесина: {wood}
"""

# Коробки
INVENTORY_BOXES = """
🎒КОРОБКИ
├📦[🆓] Free: {free_boxes}
├📦[🏡] Ферма: {farm_boxes}
├📦[💼] Рябота: {work_boxes}
├📦[💠] RBTC: {rbtc_boxes}
├📦[🏕] Вылазки: {expedition_boxes}
├📦[🥊] Схватки: {fight_boxes}
├📦[🏇] Скачки: {race_boxes}
├📦[🎫] Допуски: {pass_boxes}
└─🔑 Ключи: {keys}
"""

# === МЕНЮ ЛИДЕРОВ ===
LEADERBOARD_MENU = """
〰️〰️ 🏆 ЛИДЕРЫ ℹ️ 〰️〰️

👑 ЛЕГЕНДЫ & ЧЕМПИОНЫ 👑
├[🏡] {top_farmer}
├[💼] {top_employer}
├[⚖️] {top_trader}
├[🏕] {top_explorer}
├[🎲] {top_gambler}
├[🥊] {top_fighter}
├[🏇] {top_racer}
├[💠] {top_rbtc}
└[🤝] {top_partner}
"""

# === МЕНЮ ДРУЗЕЙ ===
FRIENDS_MENU = """
👥 «РЕФЕРАЛЬНАЯ ИМПЕРИЯ» ℹ️

🔗 Ваша реф. ссылка:
https://t.me/ryabot?start={user_id}

💼 Реф Балансы:
├ 💠 RBTC: {ref_rbtc}
├ 💵 Рябаксы: {ref_ryabucks}
└ 🎟 Билеты: {ref_tickets}

💰Всего Заработано:
├─ 💠: {total_rbtc}
├─ 💵: {total_ryabucks}
└─ 🎟: {total_tickets}
〰️〰️〰️〰️
👥 Друзья: {friends_count}
🤝 Знакомые: {acquaintances_count}
🌐 Окружение: {network_count}

ℹ️ Приглашай друзей в ₽ЯБОТ и получай награды! /ref_rewards
〰️〰️〰️〰️
💠 Партнерский Пул: {partner_pool}
🌟 Рейтинг Партнера: {partner_rating}
"""

# === МЕНЮ ПРОЧЕГО ===
OTHER_MENU = """
〰️〰️ 🗄 ПРОЧЕЕ ℹ️ 〰️〰️

₽ЯБОТ — это увлекательный симулятор фермерства с социальными элементами. Стройте свою ферму, ухаживайте за животными, выращивайте урожай и торгуйте ресурсами. Нанимайте работников и распределяйте между ними обязанности!

🤖 Отправляйтесь навстречу приключениям и станьте опытным фермером!
"""

# === ТУТОРИАЛ - ИСПРАВЛЕНИЯ ===
TUTORIAL_LICENSE_BOUGHT = """
✅ *ЛИЦЕНЗИЯ ПОЛУЧЕНА!*

📜 *Лицензия Работодателя LV1* активна!

🎉 *Поздравляем! Теперь у вас есть полный доступ к острову!*

Вы можете свободно перемещаться по острову, но для продолжения развития следуйте заданиям во вкладке *👤 Житель*.

💰 *Потрачено:* 100 💵 рябаксов
*Осталось:* {remaining} 💵 рябаксов

🎯 *Следующее задание:* Наймите первого рабочего в Академии!
"""

# === ЗАГЛУШКИ ===
SECTION_UNDER_DEVELOPMENT = "🚧 Раздел находится в разработке.\nСкоро здесь появится функционал!"
ERROR_GENERAL = "❌ Произошла ошибка. Попробуйте ещё раз."