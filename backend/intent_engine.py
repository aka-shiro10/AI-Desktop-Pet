# intent_engine.py

from sentence_transformers import SentenceTransformer, util
import torch
import re
import spacy
# Load small English model for lemmatization and stop words
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

# -----------------------------------------------------------
# Preprocessing
# -----------------------------------------------------------
def preprocess_text(text: str) -> str:
    """
    Lowercase, remove punctuation, lemmatize, remove stopwords,
    normalize whitespace.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop]
    return " ".join(tokens)

# -----------------------------------------------------------
# Model
# -----------------------------------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------------------------------------
# Extended canonical commands with casual/filler variations
# -----------------------------------------------------------
COMMANDS = {
    "open_youtube": [
        "open youtube", "go to youtube", "launch youtube",
        "open up youtube for me",
        "i need to open youtube now", "oh also open youtube for me"],
    "open_chrome": [
        "open chrome", "launch chrome",
        "can you open chrome", "please open chrome"],
    "open_whatsapp": ["open whatsapp", "launch whatsapp", "start whatsapp"],
    "open_chatgpt": ["open chatgpt", "go to chatgpt", "launch chatgpt"],
    "close_current_tab": ["close current tab", "shut this tab", "please close the tab"],
    "close_all_windows": ["close all windows", "shut everything", "close all windows please"],
    "play_music": ["play music", "start music", "play some music", "i want to hear music"],
    "whats_on_screen": ["what's on screen", "describe the screen", "what do you see", "show me the screen"]
}

# Slots for apps
APP_SLOTS = {
    "open_youtube": "youtube",
    "open_chrome": "chrome",
    "open_whatsapp": "whatsapp",
    "open_chatgpt": "chatgpt",
}

# -----------------------------------------------------------
# Keyword boosting
# -----------------------------------------------------------
COMMAND_KEYWORDS = [
    "open", "close", "youtube", "chrome", "whatsapp",
    "chatgpt", "music", "tab", "windows", "play", "stop"
]

def extract_keywords(text: str) -> str:
    """Return space-separated command keywords found in text."""
    tokens = text.split()
    return " ".join([t for t in tokens if t in COMMAND_KEYWORDS])

# -----------------------------------------------------------
# Precompute embeddings for canonical commands
# -----------------------------------------------------------
command_texts = []
command_labels = []

for label, examples in COMMANDS.items():
    for ex in examples:
        clean_ex = preprocess_text(ex)
        command_texts.append(clean_ex)
        command_labels.append(label)

command_embeddings = model.encode(command_texts, convert_to_tensor=True)

# -----------------------------------------------------------
# Intent classification with sliding window & keyword boosting
# -----------------------------------------------------------
def classify_intent(user_text: str):
    """Robust semantic intent detection for continuous speech."""
    clean_text = preprocess_text(user_text)

    # 1. Sliding window: split by punctuation to handle stories
    split_chars = [".", ",", "!", "?", ";", "..."]
    windows = [clean_text]
    for char in split_chars:
        new_windows = []
        for w in windows:
            new_windows.extend([part.strip() for part in w.split(char) if part.strip()])
        windows = new_windows

    best_score = 0
    best_label = "none"
    best_window = ""

    # 2. Evaluate each window
    for window in windows:
        # Keyword boosting: append keywords to window
        keywords_text = extract_keywords(window)
        augmented_text = window + " " + keywords_text if keywords_text else window

        user_emb = model.encode(augmented_text, convert_to_tensor=True)
        cos_scores = util.cos_sim(user_emb, command_embeddings)[0]
        idx = torch.argmax(cos_scores).item()
        score = float(cos_scores[idx])

        if score > best_score:
            best_score = score
            best_label = command_labels[idx]
            best_window = window

    # 3. Threshold
    threshold = 0.5 if len(clean_text.split()) <= 5 else 0.4
    if best_score < threshold:
        return {"intent": "none", "slots": {}, "reply": "Sorry, I didn't understand that."}

    # 4. Slot extraction
    slots = {}
    if best_label in APP_SLOTS:
        slots["app"] = APP_SLOTS[best_label]

    # 5. Reply map
    reply_map = {
        "open_youtube": "Opening YouTube.",
        "open_chrome": "Opening Chrome.",
        "open_whatsapp": "Opening WhatsApp.",
        "open_chatgpt": "Opening ChatGPT.",
        "close_current_tab": "Closing the current tab.",
        "close_all_windows": "Closing all windows.",
        "play_music": "Playing music.",
        "whats_on_screen": "Let me check what I see on screen.",
        "none": "Sorry, I didn't understand that."
    }

    return {
        "intent": best_label.replace("_", " "),
        "slots": slots,
        "reply": reply_map[best_label]
    }
