from pathlib import Path

roadmap_text = """# EverQuest Augmentation Tool – Development Roadmap

## ✅ Current State
- Streamlit app deployed at: https://prax-aug-tool.streamlit.app/
- GitHub repo: https://github.com/Praxeomatic/eq-aug-tool
- Uses `/output inventory` text file directly
- Parses augment entries by slot lines (`-Slot#`)
- Matches augment `ID` to internal database (`augmentation_only_items.csv`)
- Computes total item value using user-defined stat multipliers
- Displays equipped augments in a sortable, scored table

---

## 🔧 Immediate Goals
- Add toggle to hide/show specific stats in the result table
- Visual cue or highlighting for “upgrade” candidates
- Add unequipped aug comparison if inventory file suggests placement (future detection logic)
- Allow user to download results as `.csv` or `.json`

---

## 🧱 Intermediate Goals
- Use item `loregroup` and `augslot` fields for logic on:
  - LORE-equippable constraints
  - Slot compatibility
  - Multiple copies of same aug in different slots
- Add profile versioning: current vs planned aug layout
- Add ability to save/load user weight profiles (cookie or localStorage integration)
- Support augment planning for unequipped aug libraries (future dev)

---

## 🧪 Later or Optional Goals
- Add drag-and-drop layout planner for aug visualization
- Enable slot conflict warnings (e.g., 2 LORE augs equipped)
- Support hybrid mode: parse EQ inventory and sync with Raidloot scrape
- Implement multi-character management via save states
"""

# Save to file
roadmap_path = Path("/mnt/data/ROADMAP.md")
roadmap_path.write_text(roadmap_text)

roadmap_path.name
