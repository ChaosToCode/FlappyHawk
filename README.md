# Flappy Hawk

A retro-style Flappy Bird clone built with Pygame. Features drawn graphics (no external assets), parallax city background with vines, and a local leaderboard.

## Requirements

- Python 3.7+
- Pygame 2.0+

## Installation

```bash
pip install -r requirements.txt
```

## How to Play

```bash
python main.py
```

**Controls:**
- **SPACE** - Jump / Restart after game over
- Close window to quit

## Project Structure

```
Flappy/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── README.md
├── src/
│   ├── __init__.py
│   └── game.py          # Main game logic
├── assets/
│   ├── images/          # (placeholder for future sprites)
│   └── sounds/          # (placeholder for future audio)
└── data/
    └── leaderboard.json # High scores (auto-generated)
```

## Features

- Retro pixel-art style hawk character
- Procedurally generated city background with parallax scrolling
- Vine-covered buildings aesthetic
- Local high score leaderboard (top 5)
- Name entry for new high scores
