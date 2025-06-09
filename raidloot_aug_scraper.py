import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Update this to match your actual path if needed
with open("C:/Users/b/Desktop/everquest_tool/raidloot_scraper_urls.txt", "r", encoding="utf-8") as f:
    raw_lines = f.readlines()

# Parse into (expansion, url) pairs
expansion_urls = []
current_expansion = None
for line in raw_lines:
    line = line.strip()
    if not line:
        continue
    if line.endswith(":"):
        current_expansion = line.rstrip(":").strip()
    elif line.startswith("http"):
        expansion_urls.append((current_expansion, line))

def fetch_html(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch: {url}")
            return None
        return BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"Exception for {url}: {e}")
        return None

def parse_item_div(div, expansion):
    item = {"Expansion": expansion}
    item["ID"] = int(div.get("data-id", -1))
    item["Name"] = div.find("span", class_="itemname").text.strip()
    aug_type = next((note.text for note in div.find_all("span", class_="note") if "Aug:" in note.text), "")
    item["AugType"] = aug_type.replace("Aug:", "").strip()
    img_tag = div.find("img", class_="itemicon")
    item["IconURL"] = "https:" + img_tag["src"] if img_tag else ""
    item["ItemFlags"] = [flag.text.strip() for flag in div.find_all("span", class_="itemflag")]
    item["IsLore"] = "LORE" in item["ItemFlags"]

    labels = div.find_all("label")
    for label in labels:
        text = label.text.strip().upper().rstrip(":")
        if text == "SLOT":
            item["SlotCompat"] = label.next_sibling.strip() if label.next_sibling else ""
        elif text == "RESTRICTIONS":
            item["EquipRestrictions"] = label.next_sibling.strip() if label.next_sibling else ""
        elif text == "CLASS":
            item["ClassList"] = label.next_sibling.strip().split(",") if label.next_sibling else []
        elif text.startswith("REQUIRED LEVEL OF"):
            value = text.split()[-1].rstrip(".")
            item["RequiredLevel"] = int(value) if value.isdigit() else None

    for stat in ["AC", "HP", "MANA", "END", "ATK"]:
        match = div.find("label", string=lambda s: s and s.strip().upper().startswith(stat))
        val = match.find_next("span") if match else None
        item[stat] = int(val.text.strip().split()[0]) if val and val.text.strip().split()[0].isdigit() else 0

    heroics = {"STR": "HStr", "STA": "HSta", "AGI": "HAgi", "DEX": "HDex", "WIS": "HWis", "INT": "HInt", "CHA": "HCha"}
    for label in div.find_all("label"):
        key = label.text.strip().rstrip(":").upper()
        if key in heroics:
            heroic = label.find_next("span", class_="heroic")
            item[heroics[key]] = int(heroic.text.strip().replace("+", "")) if heroic else 0
    for v in heroics.values():
        item.setdefault(v, 0)

    for res in ["FIRE", "COLD", "MAGIC", "POISON", "DISEASE"]:
        lbl = div.find("label", string=lambda s: s and f"SV {res}" in s.upper())
        val = lbl.next_sibling.strip() if lbl and lbl.next_sibling else None
        item[f"SV{res.capitalize()}"] = int(val) if val and val.isdigit() else 0

    focus_label = div.find("label", string=lambda s: s and "Focus Effect" in s)
    if focus_label:
        focus_name = focus_label.find_next("a")
        focus_desc = focus_label.find_next("span", class_="spelldesc")
        item["FocusEffectName"] = focus_name.text.strip() if focus_name else ""
        item["FocusEffectDesc"] = focus_desc.text.strip() if focus_desc else ""

    return item

# Scrape all URLs
results = []
seen_ids = set()

for expansion, url in expansion_urls:
    print(f"Scraping {expansion}: {url}")
    soup = fetch_html(url)
    if soup is None:
        continue
    divs = soup.select("div.item.augment")
    for div in divs:
        aug_id = int(div.get("data-id", -1))
        if aug_id in seen_ids:
            continue
        seen_ids.add(aug_id)
        parsed = parse_item_div(div, expansion)
        results.append(parsed)
    time.sleep(1.0)

# Save to CSV
df = pd.DataFrame(results)
df.to_csv("all_augmentations.csv", index=False)
print("✅ Saved to all_augmentations.csv")
