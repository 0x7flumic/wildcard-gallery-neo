# Wildcard Gallery Neo

**Wildcard Gallery Neo** is a lightweight visual wildcard manager and dynamic prompt expansion engine for SD WebUI Forge (Neo). It integrates directly into the Extra Networks tab to provide a smooth, card-based interface for browsing, inserting, previewing, and batch-managing wildcard collections.

---

## ⚡ Key Highlights & Architecture

- **Visual Extra Networks Integration:** Browse wildcards as interactive cards with subfolder navigation in txt2img and img2img.
- **Zero External Dependencies:** Self-contained wildcard parsing and substitution engine—no additional extension required.
- **Dynamic Syntax Engine:** Native support for standard wildcards (`__name__`), variants (`{optA|optB}`), weighted variants (`{5::cat|1::dog}`), and sampling (`__3$$colors__` / `__3$$, $$colors__`).
- **YAML & TXT Dual Support:** Supports both flat text files (`.txt`) and deeply nested hierarchical structures (`.yaml` / `.yml`).
- **Preview Manager:** Integrated txt2img utility to batch-generate, optimize, collect, and delete visual card previews.
- **Fast-Path Engine:** Regex check bypass when prompts contain no wildcard tokens (`__` or `{`).

---

## 📥 Installation

1. Open Stable Diffusion WebUI Forge.
2. Navigate to **Extensions** → **Install from URL**.
3. Paste the URL of this repository:
   ```text
   https://github.com/0x7flumic/wildcard-gallery-neo.git
   ```
4. Click **Install**.
5. Restart the WebUI completely.

---

## 📂 Wildcard File Formats & Organization

All wildcard files reside in:
```text
extensions/wildcard-gallery-neo/wildcards/
```

### 1. Plain Text Lists (`.txt`)
Each non-empty, non-comment line is treated as an option.
- **File:** `wildcards/lighting/cinematic.txt`
  ```text
  # Atmospheric lighting styles
  dramatic volumetric lighting
  soft rim light, moody ambient glow
  high contrast chiaroscuro
  neon reflections on wet pavement
  ```
- **Prompt Usage:** `__lighting/cinematic__`

### 2. Structured Dictionaries (`.yaml` / `.yml`)
Organize categories and subcategories in a single file:
- **File:** `wildcards/characters.yaml`
  ```yaml
  roles:
    fantasy:
      - brave knight in plate armor
      - mysterious elven mage
      - shadow rogue with daggers
    scifi:
      - cybernetic bounty hunter
      - orbital mech pilot
  ```
- **Prompt Usage:**
  - `__characters/roles/fantasy__`
  - `__characters/roles/scifi__`

---

## 🎨 Preview Manager & Actions

Under **txt2img** → **Scripts** dropdown, select **Wildcard Gallery Neo Preview Manager**:

- **Target Selection:** Choose specific wildcards from the multiselect dropdown or check **Use Wildcard Branch Selector** to pick entire subfolders.
- **Insertion Modes:**
  - `AFTER`: Appends wildcard to the prompt.
  - `BEFORE`: Prepends wildcard to the prompt.
  - `SEARCH & REPLACE`: Substitutes custom placeholder text with the active wildcard.
- **Override Previews:** Re-generate previews for cards that already have existing thumbnails.
- **Batch Actions:**
  - `📊 Count Selected`: Displays the total count of wildcards matching the selection.
  - `📥 Collect Previews`: Copies matching preview images into `COLLECTED_PREVIEWS/`.
  - `⚡ Optimize Previews`: Resizes and compresses stored preview images down to standard 512px thumbnails to reclaim storage and browser memory.
  - `🗑️ Delete Previews`: Safely removes preview images for the selected wildcard cards.

---

## 🖼️ Card Customization

- Missing previews automatically display the fallback thumbnail (`resources/no-preview.jpg`).
- Custom preview images can be manually placed into `extensions/wildcard-gallery-neo/cards/` matching the relative path of the wildcard (e.g., `cards/lighting/cinematic.jpg`). Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`.

---

## 📜 Credits

Special thanks and attributions:
- **[navimixu/wildcard-gallery](https://github.com/navimixu/wildcard-gallery)** — Original visual gallery concept.
- **[adieyal/sd-dynamic-prompts](https://github.com/adieyal/sd-dynamic-prompts)** — Inspiration for dynamic syntax patterns.