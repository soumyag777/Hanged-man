"""
Petal Hangman, written in Python and run in the browser with PyScript.

Practice spots:
  - lists: the word bank, the wrong guesses, the alphabet
  - strings: hiding and revealing letters in the secret word
  - sets: remembering which letters were already guessed
"""

import random
import string

# ---------------------------------------------------------------
# game logic (plain Python, no browser stuff in this part)
# ---------------------------------------------------------------

WORD_BANK = {
    "sweet treats 🧁": ["cupcake", "macaron", "donut", "cookie", "pudding", "mochi", "waffle", "sundae"],
    "cute animals 🐾": ["bunny", "kitten", "panda", "hamster", "penguin", "otter", "koala", "puppy"],
    "in the garden 🌷": ["tulip", "daisy", "sunflower", "lavender", "clover", "blossom", "peony"],
    "cozy things ☁️": ["blanket", "pillow", "candle", "sweater", "teacup", "rainbow", "pajamas"],
}

MAX_LIVES = 6  # one life per petal


def pick_word():
    """Choose a random category, then a random word from it."""
    category = random.choice(list(WORD_BANK.keys()))
    word = random.choice(WORD_BANK[category])
    return category, word


def masked_word(secret, guessed):
    """Turn 'bunny' + {'n'} into '_ _ n n _'."""
    return " ".join(letter if letter in guessed else "_" for letter in secret)


def is_solved(secret, guessed):
    """True when every letter in the word has been guessed."""
    return all(letter in guessed for letter in secret)


class Game:
    def __init__(self):
        self.category, self.secret = pick_word()
        self.guessed = set()   # every letter tried so far
        self.wrong = []        # letters that were NOT in the word, in order

    @property
    def lives(self):
        return MAX_LIVES - len(self.wrong)

    @property
    def won(self):
        return is_solved(self.secret, self.guessed)

    @property
    def lost(self):
        return self.lives <= 0

    @property
    def over(self):
        return self.won or self.lost

    def guess(self, letter):
        """Returns 'right', 'wrong', 'repeat', or 'over'."""
        letter = letter.lower()
        if self.over:
            return "over"
        if letter in self.guessed:
            return "repeat"
        self.guessed.add(letter)
        if letter in self.secret:
            return "right"
        self.wrong.append(letter)
        return "wrong"


# ---------------------------------------------------------------
# browser part (PyScript connects Python to the page)
# ---------------------------------------------------------------

from pyscript import document, window
from pyodide.ffi import create_proxy

game = None
wins = 0
streak = 0

CHEERS = ["nice! 🌟", "yes!! 💕", "you got it ✨", "ooh good one 🌸"]
OOPS = ["oh no, a petal! 🍃", "not that one 🥺", "hmm, try again 💭"]
FACES = ["😵", "😢", "😟", "😕", "🙂", "😊", "😊"]  # index = lives left


def el(id_):
    return document.getElementById(id_)


def draw_word():
    """Build one slot per letter, showing guessed letters."""
    html = []
    for letter in game.secret:
        if letter in game.guessed:
            html.append(f'<div class="slot shown">{letter}</div>')
        elif game.lost:
            # reveal what they missed when the game ends
            html.append(f'<div class="slot missed">{letter}</div>')
        else:
            html.append('<div class="slot"></div>')
    el("word").innerHTML = "".join(html)


def draw_keyboard():
    html = []
    for letter in string.ascii_lowercase:
        cls = "key"
        if letter in game.guessed:
            cls += " right" if letter in game.secret else " wrong"
        disabled = "disabled" if (letter in game.guessed or game.over) else ""
        html.append(f'<button class="{cls}" data-letter="{letter}" {disabled}>{letter}</button>')
    el("keyboard").innerHTML = "".join(html)


def draw_flower():
    for i in range(MAX_LIVES):
        petal = el(f"petal{i}")
        # petals fall off one by one as wrong guesses pile up
        if i < len(game.wrong):
            petal.classList.add("fall")
        else:
            petal.classList.remove("fall")
    el("center").textContent = FACES[game.lives] if not game.won else "🥰"


def draw_stats():
    el("stats").textContent = f"wins: {wins} · streak: {streak}"


def say(text):
    el("message").textContent = text


def confetti():
    bits = ["🌸", "💖", "✨", "🌷", "🎀"]
    for _ in range(28):
        c = document.createElement("div")
        c.className = "confetti"
        c.textContent = random.choice(bits)
        c.style.left = f"{random.random() * 100}vw"
        c.style.animationDuration = f"{2 + random.random() * 2}s"
        c.style.animationDelay = f"{random.random() * 0.5}s"
        document.body.appendChild(c)
        window.setTimeout(create_proxy(lambda node=c: node.remove()), 4500)


def play(letter):
    global wins, streak
    result = game.guess(letter)

    if result == "repeat":
        say(f"you already tried '{letter.upper()}' 💭")
        return
    if result == "over":
        return

    say(random.choice(CHEERS) if result == "right" else random.choice(OOPS))

    if game.won:
        wins += 1
        streak += 1
        say("you saved the flower! 🌸🎉")
        el("flower").classList.add("won")
        confetti()
    elif game.lost:
        streak = 0
        say(f"the flower wilted 🥀 the word was '{game.secret}'")

    draw_word()
    draw_keyboard()
    draw_flower()
    draw_stats()


def new_game(event=None):
    global game
    game = Game()
    el("category").textContent = game.category
    el("flower").classList.remove("won")
    say(f"{len(game.secret)} letters · {MAX_LIVES} petals")
    draw_word()
    draw_keyboard()
    draw_flower()
    draw_stats()


def on_key_click(event):
    letter = event.target.getAttribute("data-letter")
    if letter:
        play(letter)


def on_key_press(event):
    key = event.key.lower()
    if len(key) == 1 and key in string.ascii_lowercase:
        play(key)
    elif key == "enter" and game.over:
        new_game()


# hook everything up
el("keyboard").addEventListener("click", create_proxy(on_key_click))
el("newBtn").addEventListener("click", create_proxy(new_game))
document.addEventListener("keydown", create_proxy(on_key_press))

new_game()
el("loading").classList.add("done")  # python is ready, hide the loading screen
