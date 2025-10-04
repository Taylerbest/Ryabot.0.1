# interfaces/telegram_bot/localization/locales/en.py
"""
English texts for bot
"""

TEXTS = {
    # Main menu buttons
    "btn_enter_island": "🏝 Enter Island",
    "btn_settings": "⚙️ Settings", 
    "btn_support": "🆘 Support",
    "btn_back": "🔙 Back",
    
    # Island buttons
    "btn_farm": "🐔 Farm",
    "btn_town": "🏘️ Town", 
    "btn_citizen": "👤 Citizen",
    "btn_work": "💼 Work",
    "btn_inventory": "🎒 Inventory",
    "btn_friends": "👥 Friends",
    "btn_leaderboard": "🏆 Leaderboard",
    "btn_other": "📋 Other",
    "btn_leave_island": "🚪 Leave Island",
    
    # Town buttons  
    "btn_townhall": "🏛️ Town Hall",
    "btn_market": "🏪 Market",
    "btn_academy": "🎓 Academy",
    "btn_ryabank": "🏦 RyaBank",
    "btn_products": "📦 Products",
    "btn_pawnshop": "💰 Pawn Shop",
    "btn_tavern": "🍺 Tavern",
    "btn_entertainment": "🎪 Entertainment",
    "btn_realestate": "🏠 Real Estate",
    "btn_vetclinic": "🏥 Vet Clinic",
    "btn_construction": "🏗️ Construction",
    "btn_hospital": "🏥 Hospital",
    "btn_quantumhub": "⚛️ Quantum Hub",
    "btn_cemetery": "⚰️ Cemetery",
    
    # Academy buttons
    "btn_labor_exchange": "💼 Labor Exchange",
    "btn_expert_courses": "🎓 Expert Courses",
    "btn_training_class": "📚 Training Class",
    "btn_hire_worker": "👷 Hire Worker",
    "btn_hire_specialist": "🧑‍🔬 Hire Specialist",
    
    # Tutorial buttons
    "btn_tutorial_start": "🚀 Start Adventure",
    "btn_tutorial_next": "➡️ Next",
    "btn_tutorial_skip": "⏭️ Skip",
    "btn_tutorial_complete": "✅ Complete",
    
    # Settings buttons
    "btn_change_language": "🌍 Change Language",
    "btn_notifications": "🔔 Notifications",
    "btn_change_character": "👤 Change Character",
    "btn_help": "ℹ️ Help",
    "btn_promo": "🎁 Promo Codes",
    "btn_quantum_pass": "💠 Quantum Pass",
    
    # Start texts
    "welcome_title": "🏝️ Welcome to Ryabot Island!",
    "welcome_stats": (
        "🤖 Bot uptime: {uptime_text}\n"
        "🏝 Islanders: {total_users}\n"
        "🟢 Now Playing: {online_users}\n"
        "1️⃣ New/Day: {new_today}\n"
        "📅 New/Month: {new_month}\n"
        "🪪 Q-Pass holders: {qpass_holders}\n"
    ),
    "uptime_format": "{days}d {hours}h {minutes}m",
    "uptime_format_short": "{hours}h {minutes}m",
    
    # Language selection
    "language_selection": (
        "🌍 Welcome!\n\n"
        "Please choose your language:\n"
        "Пожалуйста, выберите язык:"
    ),
    "language_changed": "✅ Language changed!",
    "language_changed_success": "✅ Language successfully changed to English!",
    
    # Island
    "island_welcome": (
        "🏝️ **Ryabot Island**\n\n"
        "Welcome, {username}!\n"
        "🆙 Level: {level} | 📊 XP: {experience}\n\n"
        "💰 **Resources:**\n"
        "💵 Ryabucks: {ryabucks:,}\n"
        "💠 RBTC: {rbtc:.4f}\n"
        "⚡ Energy: {energy}/{energy_max}\n\n"
        "🎮 Choose action:"
    ),
    
    # Profile
    "profile_text": (
        "👤 **Player Profile**\n\n"
        "🆔 {username} (ID: {user_id})\n"
        "🆙 Level {level} | 📊 XP: {experience}\n\n"
        "💰 **Resources:**\n"
        "💵 {ryabucks:,} ryabucks\n"
        "💠 {rbtc:.4f} RBTC\n"
        "⚡ {energy}/{energy_max} energy\n"
        "🧪 {liquid_experience} liquid XP\n"
    ),
    
    # Tutorial - Shipwreck
    "tutorial_shipwreck": (
        "⛈️ **SHIPWRECK**\n\n"
        "🚢 Your ship caught in a terrible storm...\n"
        "⚡ Lightning tears the sky, waves swallow the deck!\n\n"
        "💥 CRASH! The ship hits the rocks!\n"
        "🌊 You lose consciousness...\n\n"
        "🆘 What to do?"
    ),
    
    "tutorial_wake_up": (
        "🏖️ **AWAKENING**\n\n"
        "☀️ The sun blinds your eyes... You slowly regain consciousness.\n"
        "🏝️ Around - an unfamiliar tropical island!\n\n"
        "🤕 Your head hurts, but you're alive.\n"
        "👀 Looking around, you see ship wreckage on the shore.\n\n"
        "🚶‍♂️ Need to explore the island and find a way to survive!"
    ),
    
    "tutorial_explore": (
        "🌴 **ISLAND EXPLORATION**\n\n"
        "🚶‍♂️ You begin exploring the island.\n"
        "🏞️ Beautiful beaches, dense jungles, tall mountains...\n\n"
        "🔍 Searching for food and water, you stumble upon an abandoned village.\n"
        "🏠 Houses are empty but in good condition.\n\n"
        "💡 Maybe here you can build a new life?"
    ),
    
    "tutorial_find_resources": (
        "📦 **FIRST RESOURCES**\n\n"
        "🔍 Searching the village, you find:\n"
        "💵 100 ryabucks in an old chest\n"
        "⚡ 30 energy units\n"
        "🧪 Some liquid experience\n\n"
        "💭 'This should be enough to start...'\n\n"
        "🎯 **Your goal:** Develop the island and find a way to contact civilization!"
    ),
    
    "tutorial_hire_worker": (
        "👷 **FIRST RESIDENT**\n\n"
        "🚶‍♂️ Walking around the island, you meet a local resident!\n"
        "👋 'Hello, stranger! I saw your ship crash.'\n\n"
        "💬 'My name is Jack. I can help you develop the island'\n"
        "💰 'if you pay me 30 ryabucks.'\n\n"
        "🤝 Hire Jack? He'll become your first worker!"
    ),
    
    "tutorial_training": (
        "📚 **RESIDENT TRAINING**\n\n"
        "👷 Jack is ready to work!\n"
        "🎓 'Want me to learn some profession?'\n\n"
        "💡 You can train him as:\n"
        "👩‍🌾 **Farmer** - will grow food\n"
        "🏗️ **Builder** - will construct buildings\n"
        "🎣 **Fisherman** - will catch fish\n\n"
        "🏆 Trained specialists work more efficiently!"
    ),
    
    "tutorial_complete": (
        "🎉 **WELCOME TO RYABOT ISLAND!**\n\n"
        "✅ You successfully completed the tutorial!\n"
        "🏝️ Now you're a full-fledged island resident.\n\n"
        "🎁 **Tutorial rewards:**\n"
        "💵 +200 ryabucks\n"
        "⚡ +20 energy\n"
        "📊 +50 experience\n\n"
        "🚀 Good luck developing your island!"
    ),
    
    # Academy
    "academy_welcome": (
        "🎓 **ISLAND ACADEMY**\n\n"
        "Welcome to the education center!\n\n"
        "👷 **Your workers:** {laborers}\n"
        "🎓 **Currently training:** {training}\n"
        "🧑‍🔬 **Specialists:** {specialists}\n\n"
        "Choose action:"
    ),
    
    "labor_exchange": (
        "💼 **LABOR EXCHANGE**\n\n"
        "👷 **Workers:** {laborers}\n"
        "👥 **Total hired:** {total_workers}\n\n"
        "💰 **Hiring status:**\n"
        "{status}\n\n"
        "🎯 Workers are the foundation of your economy!"
    ),
    
    "hire_status_ready": "✅ Ready to hire (cost: {cost} ryabucks)",
    "hire_status_cooldown": "⏰ Cooldown: {hours}h {minutes}m",
    "hire_status_limit": "❌ Limit reached (need house)",
    "hire_status_unknown": "❓ Unknown error",
    
    "expert_courses": (
        "🎓 **EXPERT COURSES**\n\n"
        "👷 **Available workers:** {laborers}\n"
        "📚 **Training slots:** {slots_used}/{slots_total}\n\n"
        "💡 Turn simple workers into experts:\n"
        "👩‍🌾 **Farmer** - animal husbandry and farming\n"
        "🏗️ **Builder** - building construction\n"
        "🎣 **Fisherman** - sea fishing\n"
        "🌲 **Forester** - wood harvesting\n\n"
        "Choose specialization:"
    ),
    
    "training_class_empty": (
        "📚 **TRAINING CLASS**\n\n"
        "🎓 Nobody is training right now.\n\n"
        "💡 Send workers to expert courses!"
    ),
    
    "training_class_active": (
        "📚 **TRAINING CLASS**\n\n"
        "📊 **Slots:** {slots_used}/{slots_total}\n\n"
        "🎓 **Training:**\n"
        "{training_list}\n\n"
        "⏰ Training will take some time."
    ),
    
    # Hiring messages
    "hire_worker_success": "🎉 Worker successfully hired! You now have {count} workers.",
    "hire_worker_cooldown": "⏰ Wait {time} until next hire.",
    "hire_worker_no_money": "💰 Not enough ryabucks! Need {cost}.",
    "hire_worker_limit": "🏠 Need to build more houses for workers.",
    
    # Training messages
    "training_started": "🎓 {profession} training started! Time: {duration}",
    "training_completed": "✅ Training completed! {count} specialists ready to work.",
    "training_no_workers": "👷 No free workers for training.",
    "training_no_slots": "📚 All training slots are occupied.",
    
    # Errors
    "error_init": "❌ Initialization error occurred. Try /start",
    "error_profile": "❌ Profile loading error",
    "error_enter_island": "❌ Island entry error",
    "error_general": "❌ An error occurred. Please try again.",
    
    # Other texts
    "farm_text": "🐔 **FARM** - section under development",
    "town_text": "🏘️ **TOWN** - choose building",
    "work_text": "💼 **WORK** - section under development", 
    "inventory_text": "🎒 **INVENTORY** - section under development",
    "friends_text": "👥 **FRIENDS** - section under development",
    "leaderboard_text": "🏆 **LEADERBOARD** - section under development",
    "other_text": "📋 **OTHER** - additional functions",
    "settings_text": "⚙️ **SETTINGS** - bot settings",
    "support_text": "🆘 **SUPPORT** - help and support",
    
    # Placeholders
    "menu_placeholder": "🎯 Choose action - build, develop, earn!",
    
    # Buildings (stubs)
    "building_townhall": "🏛️ **TOWN HALL** - island management",
    "building_market": "🏪 **MARKET** - resource trading", 
    "building_ryabank": "🏦 **RYABANK** - currency exchange",
    "building_products": "📦 **PRODUCTS** - item shop",
    "building_pawnshop": "💰 **PAWN SHOP** - item buyback",
    "building_tavern": "🍺 **TAVERN** - rest and entertainment",
    "building_entertainment": "🎪 **ENTERTAINMENT** - games and contests",
    "building_realestate": "🏠 **REAL ESTATE** - land purchase",
    "building_vetclinic": "🏥 **VET CLINIC** - animal treatment",
    "building_construction": "🏗️ **CONSTRUCTION** - building construction",
    "building_hospital": "🏥 **HOSPITAL** - resident treatment",
    "building_quantumhub": "⚛️ **QUANTUM HUB** - Quantum Pass",
    "building_cemetery": "⚰️ **CEMETERY** - memory of the departed",
}