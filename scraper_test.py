import requests
from bs4 import BeautifulSoup
import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_html(url):
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise Exception(f"Request failed: {res.status_code}")
    return BeautifulSoup(res.text, "html.parser")

def parse_item_div(div):
    item = {}
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

# === Run the scraper for one page ===
url = "https://www.raidloot.com/items?name=&class=&slot=&type=Augmentation&augslot=&level=&source=RoF&prestige=Include&order=ID&view=List"
soup = fetch_html(url)
divs = soup.select("div.item.augment")
data = [parse_item_div(div) for div in divs]

# Save result
df = pd.DataFrame(data)
df.to_csv("rof_augmentations.csv", index=False)
print("Saved to rof_augmentations.csv")
