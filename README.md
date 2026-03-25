# 🏰 Magic Dungeon – Multiplayer Classroom Game

A real-time multiplayer dungeon escape game built with **Flask** and **Socket.IO**, designed for classroom use.

Players join a lobby, and once the game starts, each round presents a dungeon with a random correct exit. Everyone picks a direction — when all answers are in, a results table reveals who found the way out and who didn't. First to clear all 5 dungeons wins! 🏆

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?logo=flask)
![Socket.IO](https://img.shields.io/badge/Socket.IO-4.x-black?logo=socketdotio)

---

## ✨ Features

- **Real-time multiplayer** — powered by WebSockets (Socket.IO)
- **Live lobby** — see players join in real time with a progress bar
- **Round-based gameplay** — each round has a random correct exit (front / back / left / right)
- **Results table** — shows all players' choices and who got it right after each round
- **Leaderboard** — tracks dungeon progress across rounds
- **Game over screen** — trophy & final rankings when someone clears all dungeons
- **Player limits** — minimum 3, maximum 20 players
- **Responsive dark theme UI** 🌙

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone the repo
git clone https://github.com/Ristwolf/dungeon_py_game.git
cd dungeon_py_game

# Install dependencies
pip install flask flask-socketio

# Run the server
python game.py
```

Open **https://ristwolf.com.br/py_dungeon** in your browser.

---

## 🎮 How to Play

1. **Welcome page** — Enter your name and join the session
2. **Lobby** — Wait for at least 3 players, then the host clicks **Start Game**
3. **Each round** — A dungeon appears with 4 direction buttons. Pick the exit you think is correct!
4. **Results** — Once everyone answers, a table shows who was right ✅ and who was wrong ❌
5. **Win** — First player to escape all 5 dungeons wins the game!

---

## 📁 Project Structure

```
├── game.py                  # Flask + SocketIO server & game logic
├── templates/
│   ├── welcome.html         # Landing page (name input)
│   ├── lobby.html           # Live player lobby
│   └── game.html            # Main game UI
├── static/
│   └── css/
│       ├── welcome.css      # Welcome page styles
│       ├── lobby.css        # Lobby styles
│       └── game.css         # Game styles
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

You can tweak the game settings at the top of `game.py`:

| Setting | Default | Description |
|---|---|---|
| `MIN_PLAYERS` | `3` | Minimum players to start a game |
| `MAX_PLAYERS` | `20` | Maximum players allowed |
| `TOTAL_DUNGEONS` | `5` | Number of dungeons to escape to win |
| `DIRECTIONS` | `["front", "back", "left", "right"]` | Possible exit directions |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Flask-SocketIO
- **Frontend:** HTML, CSS, JavaScript, Socket.IO client
- **Real-time:** WebSockets via Socket.IO

---

## 📄 License

This project is open source and available for educational use.
