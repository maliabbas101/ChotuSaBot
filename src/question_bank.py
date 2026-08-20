"""Static content bank for entertainment commands — no external API required.

Each item is a plain dict/tuple so this stays trivially editable and has no
runtime dependencies. Swap in api-ninjas-backed fetchers later if desired;
nothing else in the codebase should need to change since callers only see
the shapes documented below.
"""

from __future__ import annotations

# Each: {"question": str, "answers": [accepted lowercase strings], "category": str}
TRIVIA_QUESTIONS: list[dict] = [
    {
        "question": "What is the capital of Pakistan?",
        "answers": ["islamabad"],
        "category": "Geography",
    },
    {
        "question": "What is the national language of Pakistan?",
        "answers": ["urdu"],
        "category": "Culture",
    },
    {
        "question": "In what year did Pakistan gain independence?",
        "answers": ["1947"],
        "category": "History",
    },
    {
        "question": "What is the highest mountain in Pakistan?",
        "answers": ["k2", "mount godwin austen", "godwin austen"],
        "category": "Geography",
    },
    {
        "question": "Which sea borders Pakistan's southern coast?",
        "answers": ["arabian sea"],
        "category": "Geography",
    },
    {
        "question": "What is the currency of Pakistan?",
        "answers": ["rupee", "pakistani rupee", "pkr"],
        "category": "General",
    },
    {
        "question": "How many players are on a cricket team on the field at once?",
        "answers": ["11", "eleven"],
        "category": "Sports",
    },
    {
        "question": "What gas do plants primarily absorb for photosynthesis?",
        "answers": ["carbon dioxide", "co2"],
        "category": "Science",
    },
    {"question": "What is the chemical symbol for gold?", "answers": ["au"], "category": "Science"},
    {
        "question": "How many continents are there on Earth?",
        "answers": ["7", "seven"],
        "category": "Geography",
    },
    {
        "question": "What is the largest planet in our solar system?",
        "answers": ["jupiter"],
        "category": "Science",
    },
    {
        "question": "In which city is the Badshahi Mosque located?",
        "answers": ["lahore"],
        "category": "Culture",
    },
    {
        "question": "What is the boiling point of water in Celsius?",
        "answers": ["100", "100c", "100 celsius"],
        "category": "Science",
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "answers": ["mars"],
        "category": "Science",
    },
    {
        "question": "What does 'HTTP' stand for?",
        "answers": ["hypertext transfer protocol"],
        "category": "Tech",
    },
]

# Each: {"riddle": str, "answer": [accepted lowercase strings]}
RIDDLES: list[dict] = [
    {
        "riddle": (
            "I speak without a mouth and hear without ears. I have no body, "
            "but I come alive with wind. What am I?"
        ),
        "answers": ["echo", "an echo"],
    },
    {
        "riddle": "The more you take, the more you leave behind. What am I?",
        "answers": ["footsteps", "footprints"],
    },
    {"riddle": "What has keys but can't open locks?", "answers": ["piano", "a piano", "keyboard"]},
    {
        "riddle": "I'm tall when I'm young and short when I'm old. What am I?",
        "answers": ["candle", "a candle"],
    },
    {"riddle": "What has a heart that doesn't beat?", "answers": ["artichoke", "an artichoke"]},
    {
        "riddle": "What can travel around the world while staying in a corner?",
        "answers": ["stamp", "a stamp"],
    },
    {"riddle": "The more you cut me, the bigger I get. What am I?", "answers": ["hole", "a hole"]},
    {"riddle": "What has one eye but can't see?", "answers": ["needle", "a needle"]},
    {"riddle": "What gets wetter the more it dries?", "answers": ["towel", "a towel"]},
    {
        "riddle": "I have branches but no fruit, trunk, or leaves. What am I?",
        "answers": ["bank", "a bank"],
    },
]

WOULD_YOU_RATHER: list[str] = [
    "Would you rather have chai every day for a year or biryani every day for a year?",
    "Would you rather lose your phone for a week or lose internet for a month?",
    "Would you rather be able to fly or be invisible?",
    "Would you rather always be 10 minutes late or always be 20 minutes early?",
    "Would you rather give up rice or give up roti?",
    "Would you rather have unlimited data but slow speed, or fast speed with a strict limit?",
    "Would you rather live without AC in Quetta summers or without a heater in Quetta winters?",
    "Would you rather binge-watch a series in one night or spread it over a month?",
    "Would you rather only text in voice notes forever or only in memes forever?",
    "Would you rather have free load-shedding-proof electricity or free unlimited mobile data?",
]

QOTD_PROMPTS: list[str] = [
    "What's the best chai spot you've ever been to?",
    "What's one skill you wish you'd learned earlier?",
    "What's your go-to comfort food?",
    "What's a song that instantly puts you in a good mood?",
    "What's the most useless talent you have?",
    "If you could time travel to any decade, which one and why?",
    "What's a small thing that makes your day better?",
    "What's the last show or movie that actually surprised you?",
    "What's your unpopular opinion about food?",
    "What's one thing on your bucket list?",
]

ROAST_TEMPLATES: list[str] = [
    "{user} really said 'trust the process' and the process filed a restraining order.",
    "{user}'s wifi has better commitment issues than their group chat replies.",
    "{user} out here giving advice like they didn't just ask 'wait what does "
    "that mean' five minutes ago.",
    "{user}'s aura is giving 'left on read since 2019'.",
    "If overthinking burned calories, {user} would be an athlete.",
    "{user} types 'lol' with the same energy as a robot reading a manual.",
    "{user}'s fashion sense peaked when uniforms were mandatory.",
    "{user} argues like they're being paid per word and the pay is bad.",
]

COMPLIMENT_TEMPLATES: list[str] = [
    "{user}, you make this server genuinely better just by being in it.",
    "{user} has main-character energy and doesn't even try.",
    "Honestly {user}'s taste is so good it should be studied.",
    "{user} always shows up for people — that's rarer than it should be.",
    "{user}'s sense of humor is criminally underrated.",
    "{user} radiates the kind of calm that makes chaotic days easier.",
    "Whatever {user} is working on, it's going to turn out great.",
    "{user} is the friend everyone wishes they had on speed dial.",
]

# Optional themed content — Quetta Tea Corner has a #rekhta channel, so a
# small Urdu poetry couplet bank fits the server's culture.
REKHTA_COUPLETS: list[dict] = [
    {
        "couplet": (
            "Hazaron khwahishen aisi ke har khwahish pe dam nikle,\n"
            "Bohot niklay mere armaan lekin phir bhi kam nikle."
        ),
        "poet": "Mirza Ghalib",
    },
    {
        "couplet": (
            "Dil hi to hai na sang-o-khisht, dard se bhar na aaye kyun?\n"
            "Royenge hum hazaar baar, koi humein sataye kyun?"
        ),
        "poet": "Mirza Ghalib",
    },
    {
        "couplet": (
            "Hain aur bhi duniya mein sukhanwar bohot achhe,\n"
            "Kehte hain ke Ghalib ka hai andaz-e-bayan aur."
        ),
        "poet": "Mirza Ghalib",
    },
    {
        "couplet": "Mohabbat karne wale kam na honge,\nTeri mehfil mein lekin hum na honge.",
        "poet": "Unknown",
    },
    {
        "couplet": "Tum mere paas hote ho goya,\nJab koi doosra nahi hota.",
        "poet": "Momin Khan Momin",
    },
    {
        "couplet": (
            "Ranjish hi sahi dil hi dukhane ke liye aa,\n"
            "Aa phir se mujhe chhod ke jaane ke liye aa."
        ),
        "poet": "Ahmed Faraz",
    },
    {
        "couplet": (
            "Suna hai log usay aankh bhar ke dekhte hain,\n"
            "So uske shehar mein kuch din thehar ke dekhte hain."
        ),
        "poet": "Faiz Ahmed Faiz",
    },
]
