import json
import openai
import os
import random

# ==========================
# CONFIG
# ==========================

openai.api_key = "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"

QUESTIONS = {
    1: {
        "text": "Your friend at Hogwarts is badly hurt during a duel. What do you do?",
        "options": [
            "Rush in to protect them, no matter the risk.",
            "Stay by their side and comfort them until help arrives.",
            "Think logically and find the safest way to get help.",
            "Look for whoever caused it and make sure it never happens again."
        ]
    },
    2: {
        "text": "What do you look for most in a friend?",
        "options": [
            "Someone courageous and daring.",
            "Someone loyal who never abandons you.",
            "Someone intelligent and thoughtful.",
            "Someone ambitious and driven."
        ]
    },
    3: {
        "text": "What scares you the most?",
        "options": [
            "Failing to protect the people you care about.",
            "Being abandoned or forgotten.",
            "Making the wrong decision at a critical moment.",
            "Being overlooked and never reaching your potential."
        ]
    },
    4: {
        "text": "You must pick a magical weapon for a duel. What do you choose?",
        "options": [
            "A bold, powerful spell that charges straight in.",
            "A protective charm that shields your allies.",
            "A clever magical tool that helps you outsmart your opponent.",
            "A dark, advanced technique with immense power."
        ]
    },
    5: {
        "text": "How would you spend a Saturday night at Hogwarts?",
        "options": [
            "Exploring forbidden corridors or secret passages.",
            "Helping friends or staff with whatever they need.",
            "Studying magical theory and practicing spells.",
            "Planning long-term goals and how to achieve them."
        ]
    }
}

# ==========================
# LLM HELPERS
# ==========================

def call_llm(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def interpret_answer(question_text: str, options, user_input: str) -> str:
    prompt = load_prompt("prompts/interpret.txt")
    prompt = prompt.replace("{{question}}", question_text)
    prompt = prompt.replace("{{options}}", "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options)))
    prompt = prompt.replace("{{input}}", user_input)
    return call_llm(prompt).strip()


def update_state(state: dict, trait: str) -> dict:
    prompt = load_prompt("prompts/update_state.txt")
    prompt = prompt.replace("{{state}}", json.dumps(state))
    prompt = prompt.replace("{{trait}}", trait)

    raw = call_llm(prompt)

    cleaned = (
        raw.replace(",}", "}")
           .replace(",]", "]")
           .replace(", }", "}")
           .replace(", ]", "]")
           .replace(",\n}", "}")
           .strip()
    )
    return json.loads(cleaned)


def summarize(summary: str, question_text: str, user_input: str, trait: str) -> str:
    prompt = load_prompt("prompts/summarize.txt")
    prompt = prompt.replace("{{summary}}", summary)
    prompt = prompt.replace("{{question}}", question_text)
    prompt = prompt.replace("{{answer}}", user_input)
    prompt = prompt.replace("{{trait}}", trait)
    return call_llm(prompt)


def final_review(state: dict, summary: str) -> str:
    prompt = load_prompt("prompts/review.txt")
    prompt = prompt.replace("{{state}}", json.dumps(state))
    prompt = prompt.replace("{{summary}}", summary)
    return call_llm(prompt)


# ==========================
# STATE RESET (ALWAYS NEW GAME)
# ==========================

initial_state = {
    "turn": 0,
    "game_over": False,
    "final_house": "",
    "story_summary": "",
    "asked_questions": [],
    "house_points": {
        "gryffindor": 0,
        "hufflepuff": 0,
        "ravenclaw": 0,
        "slytherin": 0
    }
}

with open("state.json", "w") as f:
    json.dump(initial_state, f, indent=4)

state = initial_state
asked = set()        # <-- FIXED
summary = ""         # <-- FIXED

# ==========================
# INTRO
# ==========================

print("\n=== WELCOME TO HOGWARTS ===")
print(
    "You step off the Hogwarts Express and breathe in the crisp Scottish air.\n"
    "For the first time, the towering silhouette of Hogwarts Castle rises before you—ancient, mysterious, and full of magic.\n"
    "Students hurry past with trunks and pets, but you're guided into the Great Hall,\n"
    "where thousands of candles float above long wooden tables.\n"
    "The Sorting Hat waits on its stool, ready to peer into your heart and uncover your truest nature.\n"
    "Answer carefully—your destiny at Hogwarts begins now.\n"
)

# ==========================
# MAIN GAME LOOP (5 QUESTIONS)
# ==========================

all_ids = list(QUESTIONS.keys())
random.shuffle(all_ids)

for i in range(5):
    qid = all_ids[i]
    asked.add(qid)
    state["asked_questions"] = list(asked)
    state["turn"] = i + 1

    q_text = QUESTIONS[qid]["text"]
    options = QUESTIONS[qid]["options"]

    print("\n=== Sorting Hat Scene ===")
    print(q_text)
    for idx, opt in enumerate(options, start=1):
        print(f"{idx}. {opt}")

    user_input = input("\nYour answer (you can type a number or a phrase): ")

    trait = interpret_answer(q_text, options, user_input)
    print(f"[Interpreted trait: {trait}]")

    state = update_state(state, trait)
    summary = summarize(summary, q_text, user_input, trait)

# ==========================
# DETERMINE FINAL HOUSE
# ==========================

if not state.get("final_house"):
    hp = state["house_points"]
    best_house = max(hp, key=hp.get)
    state["final_house"] = best_house.capitalize()

state["game_over"] = True

# ==========================
# END OF GAME
# ==========================

print("\n=== FINAL SORTING ===")
print("House:", state["final_house"])

review = final_review(state, summary)
print("\n=== SORTING HAT REVIEW ===")
print(review)

os.makedirs("run_outputs", exist_ok=True)
with open("run_outputs/final_state.json", "w") as f:
    json.dump(state, f, indent=4)
