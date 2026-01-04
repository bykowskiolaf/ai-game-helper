# ProxiHUD 🤖

**ProxiHUD** is a lightweight, AI-powered overlay companion for video games. It uses Google's Gemini 1.5 Flash Vision model to analyze your screen in real-time and provide tactical advice, loot appraisal, mechanics explanations, and more.

While originally designed for *The Elder Scrolls Online (ESO)*, the architecture is generic enough to adapt to other MMOs or RPGs.

---

## ✨ Features

* **👁️ Smart Vision:** Instantly analyzes your screen content.
    * **Combat:** Analyzes threat levels, suggests tactics, and identifies mechanics.
    * **Inventory:** Appraises loot value and suggests what to keep/sell.
    * **Death Recap:** Explains why you died and how to avoid it next time.
* **💬 Contextual Chat:** Don't just get a report—ask follow-up questions! (e.g., *"How do I beat this boss?"* or *"Is this sword good for a tank?"*).
* **🎭 AI Personas:** Choose your companion's personality:
    * *Default, Sarcastic, Brief, Pirate, or Overly Helpful.*
* **⚙️ Unobtrusive Overlay:**
    * Runs as a transparent, "Always on Top" window.
    * **F11** to trigger a quick scan.
    * **F12** to instant-quit (panic button).
    * Draggable and resizable.
* **🔑 Multi-Key Support:** Add multiple API keys to rotate through them automatically if you hit rate limits.

---

## 🚀 Getting Started (User)

### Prerequisites
1.  **Windows 10/11** (Tested on Windows).
2.  A **Google Gemini API Key** (Free tier available).
    * [Get an API Key here](https://aistudio.google.com/app/apikey).

### Installation
1.  Go to the [Releases Page](../../releases) and download the latest `ProxiHUD.exe`.
2.  Run the executable.
3.  **First Run:** You will be prompted to enter your API Key(s).
4.  **In-Game:** Switch your game to **Windowed Borderless** mode (Fullscreen Exclusive may block the overlay).

### Usage
* **F11:** Trigger an automatic scan of the current screen.
* **Chat Box:** Type a specific question about what you see and press Enter.
* **⚙️ Settings:** Click the gear icon to change Opacity, AI Persona, or manage API Keys.

---

## 🛠️ Development Setup

If you want to contribute or build it yourself, follow these steps.

### Prerequisites
* **Python 3.10+**
* **uv** (Recommended for fast dependency management) or `pip`.

### 1. Clone the Repo
```bash
git clone [https://github.com/bykowskiolaf/ai-game-helper.git](https://github.com/bykowskiolaf/ai-game-helper.git)
cd ai-game-helper

```

### 2. Install Dependencies

Using `uv`:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 3. Run from Source

ProxiHUD detects if it is running in "Dev Mode" and will save config/logs to the local project folder instead of AppData.

```bash
python src/run.py

```

### 4. Build EXE

To create a standalone executable:

```bash
# Install PyInstaller if not already installed
uv pip install pyinstaller

# Run the build command
uv run pyinstaller --noconsole --onefile --name "ProxiHUD" --paths "src" --icon "src/proxihud/icon.ico" --hidden-import "proxihud" src/run.py

```

The output file will be in the `dist/` folder.

---

## 📂 Configuration & Data

* **Production (EXE):** Data is stored in `%LOCALAPPDATA%\ProxiHUD\`
* **Development:** Data is stored in the project root.

**Files:**

* `.env`: Stores encrypted API keys.
* `settings.json`: Stores window position, opacity, and preferences.
* `proxi_debug.log`: Application logs for troubleshooting.

---

## 🤝 Contributing

Pull requests are welcome!

1. Fork the repo.
2. Create a feature branch (`git checkout -b feature/NewThing`).
3. Commit your changes.
4. Push to the branch.
5. Open a Pull Request.
