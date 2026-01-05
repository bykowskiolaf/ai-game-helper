# ProxiHUD 🤖

**ProxiHUD** is a lightweight, AI-powered overlay companion for video games. It uses Google's **Gemini 2.0 Flash (Experimental)** model to analyze your screen in real-time *and* intelligently query your actual game data (Inventory, Quests, Build) only when needed.

While originally designed for *The Elder Scrolls Online (ESO)*, the architecture is generic enough to adapt to other MMOs or RPGs.

---

## ✨ Features

* **👁️ Smart Vision:** Instantly analyzes your screen content.
    * **Combat:** Detects boss mechanics (AOE circles, cast bars) and suggests immediate tactical counters.
    * **UI Reading:** Reads quest objectives, death recaps, and tooltips directly from the screen.
* **🧠 Deep Data Tools (In-Process MCP):**
    * **"Infinite" Context:** The AI has access to your entire inventory, bank, and quest log but only "reads" it when you ask.
    * **Smart Retrieval:** Ask *"Do I have enough materials for a potion?"* and it will check your bank automatically.
    * **Build Analysis:** Checks your slotted skills and attributes to give specific rotation advice.
* **💬 Contextual Chat:** Ask follow-up questions like *"How much is this loot worth?"* or *"Where is this quest location?"*.
* **⚙️ Unobtrusive Overlay:**
    * Runs as a transparent, "Always on Top" window.
    * **F11** to trigger a quick scan.
    * **F12** to instant-quit (panic button).
    * Draggable and resizable.
* **🔑 Resilience:** Supports multiple API keys with automatic rotation to handle rate limits gracefully.

---

## 🚀 Getting Started (User)

### Prerequisites
1.  **Windows 10/11** (Tested on Windows).
2.  A **Google Gemini API Key** (Free tier available).
    * [Get an API Key here](https://aistudio.google.com/app/apikey).
3.  **The Elder Scrolls Online** installed.

### Installation
1.  Go to the [Releases Page](../../releases) and download the latest `ProxiHUD.exe`.
2.  Run the executable.
3.  **Startup Wizard:**
    * **Step 1:** Enter your API Key(s).
    * **Step 2:** Click **"Install Bridge AddOn"**. This installs the Lua bridge that dumps your inventory/quest data to disk.
4.  **In-Game:**
    * Switch your game to **Windowed Borderless** mode.
    * **Type `/reloadui`** in chat once to generate the initial data file.

### Usage
* **F11:** Trigger an automatic scan of the current screen.
* **Chat Box:** Type a specific question (e.g., *"What is in my inventory?"*) and press Enter.
* **Right-Click Text:** If an update is available, right-click the notification to auto-update.
* **⚙️ Settings:** Click the gear icon to change Opacity or manage API Keys.

---

## 🛠️ Development Setup

If you want to contribute or build it yourself, follow these steps.

### Prerequisites
* **Python 3.11+**
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
# On Windows:
.venv\Scripts\activate
uv pip install -e .
```

### 3. Run from Source (Dev Mode)

ProxiHUD detects if it is running in "Dev Mode" and will use **Mock Data** instead of real game files.

* **Mock Data:** It reads from `mocks/ProxiHUD_Bridge.lua` instead of your Documents folder.
* **Logs:** Saved to `src/proxihud/proxi_debug.log`.

```bash
python src/run.py
```

### 4. Build EXE

To create a standalone executable for Windows:

```bash
# Install PyInstaller
uv pip install pyinstaller

# Run the build command (Windows)
uv run pyinstaller --noconsole --onefile --name "ProxiHUD" --paths "src" --icon "src/proxihud/icon.ico" --hidden-import "proxihud" --hidden-import "unicodedata" src/run.py
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
