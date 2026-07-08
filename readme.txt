# 📝 Skill Definition & Localization Automation Tool Manual

This tool automatically extracts text from the configuration files (`definitions.json`) of the `puffish_skills` mod, normalizes any mixed structural format into a clean transport object syntax, and generates localized language files ready for Minecraft resource packs.

---

## 📂 Structure & Preparation

Before running the tool, ensure your files and folders are structured as follows:

    📁 (Working Directory)
     ├ 📄 process_skills.py    (Main script: Full-syntax hybrid version)
     ├ 📄 run.bat               (Execution batch file: With mode selector)
     └ 📁 definitions           (Input folder)
        ├ 📁 1
        │  └ 📄 definitions.json
        ├ 📁 2
        │  └ 📄 definitions.json
        └ 📁 3
           └ 📄 definitions.json

> **💡 Note on Folders**
> If you add more folders (categories) or change their names to something other than numbers (e.g., `combat`, `magic`), make sure to update the `TARGET_FOLDERS = ["1", "2", "3"]` line at the top of `process_skills.py` to match your actual structure.

---

## 🔄 Standard Workflow (3 Steps)

### 【Step 1】 Choose Base Language & Patch Definitions
1. Double-click `run.bat` to launch the tool.
2. Select your base language mode first:
   * **`[1] Japanese Base`**: To extract text from custom files containing Japanese.
   * **`[2] English Base`**: To extract text from pre-existing English config files (e.g., from public modpacks).
3. Enter your desired **Identifier (e.g., `sis`)** when prompted. This acts as the prefix for your translation keys.
4. Select **`[1]`** from the menu to execute.

**✨ Automated Process & Outputs:**
* The tool targets only the `title` and `description` keys. Whether the original text was formatted as a raw string or wrapped inside a `[{"text": "..."}]` array, it automatically normalizes everything into a clean `{"translate": "Identifier.shared.xxxx"}` object structure inside `definitions_patched.json`.
* System data fields such as `rewards`, `icon`, and `cost` are kept completely untouched.
* A shared output folder named `output_[Identifier]/` will be created automatically, containing your base language file (`ja_jp.json` or `en_us.json`) along with the translation template **`blank.json`**.

---

### 【Step 2】 Translate via AI (e.g., Gemini)
1. Open the generated `output_[Identifier]/blank.json` and copy its entire content.
2. Paste it into your AI (such as Gemini) along with the following prompt:

> **🤖 AI Prompt Template**
> Please translate only the text inside the brackets of the following JSON data into natural English (or your target language) suitable for a Minecraft skill tree.
> 
> [Notes]
> * **DO NOT remove** the `"TODO: Translate [...]"` outer structure. It is required for post-processing scripts.
> * Keep all formatting tags like color codes (`§e`, `§c§l`) and newline symbols (`\n`) intact, placing them properly within the translated text.
> * DO NOT modify the keys (e.g., `"sis.shared.xxxx"`).

3. Copy the translated JSON response from the AI (ensuring it retains the `TODO: Translate [...]` structure) and overwrite/save it back into `output_[Identifier]/blank.json`.

---

### 【Step 3】 Clean TODO Tags & Output Final Lang Files
1. Launch `run.bat` again, matching your previous base mode and identifier to head back into the menu.
2. Select your output option based on the target language:
   * **Choose `[2]`**: Instantly generates the standard English file **`en_us.json`**.
   * **Choose `[3]`**: Manually type in any target language code (e.g., `zh_cn`, `ja_jp`) to output that specific file.

**✨ What gets generated:**
* Inside the `output_[Identifier]/` folder, your final language file (e.g., `en_us.json`) will be generated with all `TODO` prefixes cleanly stripped. It is completely ready to be packed into your resource pack!

---

## 🛠️ Advanced Features

### 1. Appending New Skills Safely (Incremental Updates)
Any parts already converted to `{"translate": "..."}` are recognized as processed and skipped automatically. If you add new skills later in raw text format, you can safely re-run Step 1. The script will generate new keys for the additions and append them to `blank.json` without breaking or duplicate-patching your existing data.

### 2. Hash Collision Prevention (For Massive Projects)
To keep keys clean and short, this tool defaults to a **4-digit hex hash (maximum of 65,536 patterns)** to merge identical strings. 
If your project scales up immensely, exceeding **1,000 unique string entries (approx. 15–20 pages of skills)**, you can completely eliminate the statistical risk of two different texts receiving the same key by changing the digit slice from `[:4]` to **`[:6]` (approx. 16.7 million patterns)** in `process_skills.py`:

```python
def get_text_hash(text):
    # Changing [:4] to [:6] completely eliminates the collision risk.
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:6]

2026/05/12 Omuraisu and Gemini