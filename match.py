#!/usr/bin/env python3
"""Match items between master.csv and mine.csv, finding items available in both."""

import csv
import re


def parse_master(filepath):
    """Parse master.csv and return dict of {normalized_name: (original_name, value, points)}."""
    items = {}
    with open(filepath, "r", encoding="latin-1") as f:
        reader = csv.reader(f)
        header = next(reader)  # Row 1: point headers

        # Find point value columns by parsing the header
        point_columns = {}
        for i, cell in enumerate(header):
            cell = cell.strip()
            match = re.match(r"(\d+)\s*Point", cell)
            if match:
                point_columns[i] = int(match.group(1))

        for row in reader:
            for col_idx, points in point_columns.items():
                # Each point group: name at col_idx, value at col_idx+1
                name_idx = col_idx
                val_idx = col_idx + 1
                if name_idx < len(row) and val_idx < len(row):
                    name = row[name_idx].strip()
                    val = row[val_idx].strip()
                    if name and val in ("0", "1"):
                        unavailable = int(val)
                        norm = normalize(name)
                        items[norm] = (name, unavailable, points)
    return items


def parse_mine(filepath):
    """Parse mine.csv and return list of normalized names with originals."""
    items = []
    seen = set()
    with open(filepath, "r", encoding="latin-1") as f:
        raw = f.read()

    # Handle quoted multi-line entries and single-line entries
    entries = []
    i = 0
    lines = raw.split("\n")
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('"'):
            # Multi-line quoted entry: collect until closing quote
            combined = line[1:]  # strip leading quote
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.endswith('"'):
                    combined += " " + next_line[:-1]  # strip trailing quote
                    i += 1
                    break
                else:
                    combined += " " + next_line
                    i += 1
            entries.append(combined.strip())
        else:
            entries.append(line)
            i += 1

    for entry in entries:
        norm = normalize_mine_entry(entry)
        if norm and norm not in seen:
            seen.add(norm)
            items.append((norm, entry))

    return items


def normalize(name):
    """Normalize a master.csv name for matching."""
    name = name.strip().lower()
    # Standardize common patterns
    name = re.sub(r"\s+", " ", name)
    return name


def normalize_mine_entry(entry):
    """Normalize a mine.csv entry for matching against master names."""
    entry = entry.strip()
    if not entry:
        return None

    # Handle multi-word entries that represent form variants
    # Patterns like "Rotom Heat Rotom" -> "Rotom-Heat"
    # "Vulpix Alolan Form" -> "Alolan Vulpix"
    # "Basculegion Male" -> "Basculegion-M"
    # "Articuno Galarian Form" -> "Galarian Articuno"
    # "Decidueye Hisuian Form" -> "Hisuian Decidueye"
    # "Meowstic Male" -> "Meowstic" (we'll handle gender separately)
    # "Darmanitan Galarian Form" -> "Galarian Darmanitan"
    # "Darmanitan Zen Mode" -> handled specially
    # "Darmanitan Standard Mode" -> "Darmanitan"
    # "Eiscue Ice Face" / "Eiscue Noice Face" -> "Eiscue"
    # "Silvally Type: Normal" -> "Silvally"
    # "Shaymin Land Forme" -> "Shaymin"
    # "Basculin White-Striped Form" -> "Basculin"

    name = entry.lower().strip()

    # Special multi-word patterns from mine.csv:
    # "Rotom Rotom" -> just "Rotom"
    # "Rotom Heat Rotom" -> "Rotom-Heat"
    # "Rotom Wash Rotom" -> "Rotom-Wash"
    # etc.
    rotom_match = re.match(r"rotom\s+(heat|wash|frost|fan|mow)\s+rotom", name)
    if rotom_match:
        return "rotom-" + rotom_match.group(1)
    if name == "rotom rotom":
        return "rotom"

    # "Basculegion Male" -> "Basculegion-M"
    if re.match(r"basculegion\s+male", name):
        return "basculegion-m"
    if re.match(r"basculegion\s+female", name):
        return "basculegion-f"

    # "Basculin White-Striped Form" -> "basculin"
    if re.match(r"basculin\s+white-striped", name):
        return "basculin"

    # Regional forms: "X Galarian Form" -> "Galarian X"
    regional_match = re.match(r"(.+?)\s+(galarian|alolan|hisuian|paldean)\s+form", name)
    if regional_match:
        pokemon = regional_match.group(1).strip()
        region = regional_match.group(2).strip()
        return region + " " + pokemon

    # Hisuian Form specific: "X Hisuian Form" -> "Hisuian X"
    hisuian_match = re.match(r"(.+?)\s+hisuian\s+form", name)
    if hisuian_match:
        return "hisuian " + hisuian_match.group(1).strip()

    # "Darmanitan Galarian Form" already handled above
    # "Darmanitan Zen Mode" -> skip (it's a form variant, map to galarian darmanitan)
    if re.match(r"darmanitan\s+zen\s+mode", name):
        return "galarian darmanitan"  # Zen mode is the Galarian form
    if re.match(r"darmanitan\s+standard\s+mode", name):
        return "darmanitan"

    # "Eiscue Ice Face" / "Eiscue Noice Face" -> "Eiscue"
    if re.match(r"eiscue\s+(ice|noice)\s+face", name):
        return "eiscue"

    # "Silvally Type: Normal" -> "Silvally"
    if re.match(r"silvally\s+type:", name):
        return "silvally"

    # "Shaymin Land Forme" -> "Shaymin"
    if re.match(r"shaymin\s+land\s+forme", name):
        return "shaymin"

    # "Tornadus Incarnate Forme" -> "Tornadus-Incarnate"
    forme_match = re.match(r"(tornadus|thundurus|landorus)\s+incarnate\s+forme", name)
    if forme_match:
        return forme_match.group(1) + "-incarnate"

    # "Meowstic Male" / "Meowstic Female" -> "Meowstic"
    if re.match(r"meowstic\s+(male|female)", name):
        return "meowstic"

    # "Indeedee Male" / "Indeedee Female" -> "Indeedee"
    if re.match(r"indeedee\s+(male|female)", name):
        return "indeedee"

    # "Qwilfish Hisuian Form" -> "Hisuian Qwilfish"
    # Already handled by regional match above

    # "Sliggoo Hisuian Form" -> "Hisuian Sliggoo"
    # "Goodra Hisuian Form" -> "Hisuian Goodra"
    # Already handled by regional match above

    # "Voltorb Hisuian Form" -> "Hisuian Voltorb"
    # "Electrode Hisuian Form" -> "Hisuian Electrode"
    # Already handled

    # "Sneasel Hisuian Form" -> "Hisuian Sneasel"
    # Already handled

    # "Avalugg Hisuian Form" -> "Hisuian Avalugg"
    # Already handled

    # "Zoroark Hisuian Form" -> "Hisuian Zoroark"
    # "Zorua Hisuian Form" -> handled but master might not have it directly
    # Already handled

    # "Growlithe Hisuian Form" -> "Hisuian Growlithe" (not in master as separate)
    # master has "Hisuian Arcanine" but not "Hisuian Growlithe" - check

    # "Braviary Hisuian Form" -> "Hisuian Braviary"
    # Already handled

    # "Decidueye Hisuian Form" -> "Hisuian Decidueye"
    # "Typhlosion Hisuian Form" -> "Hisuian Typhlosion"
    # "Samurott Hisuian Form" -> "Hisuian Samurott"
    # Already handled

    # "Lilligant Hisuian Form" -> "Hisuian Lilligant"
    # Already handled

    # "Stunfisk Galarian Form" -> "Galarian Stunfisk"
    # "Corsola Galarian Form" -> "Galarian Corsola"
    # Already handled

    # "Farfetch'd Galarian Form" -> "Galarian Farfetch'd"  (note the apostrophe)
    # Already handled

    # "Linoone Galarian Form" -> "Galarian Linoone" (master has this as line item? no, master has Galarian Linoone in 2-point column)
    # Actually checking master... it has "Galarian Linoone" and "Galarian Mr. Mime"

    # "Mr. Mime Galarian Form" -> "Galarian Mr. Mime"
    # Already handled

    # "Darumaka Galarian Form" -> "Galarian Darumaka" (master doesn't have this? check)
    # master has "Galarian Darmanitan" at row 4

    # "Diglett Alolan Form" -> "Alolan Diglett"
    # "Dugtrio Alolan Form" -> "Alolan Dugtrio"
    # Already handled

    # "Raichu Alolan Form" -> "Alolan Raichu"
    # Already handled

    # "Meowth Galarian Form" -> "Galarian Meowth"
    # "Meowth Alolan Form" -> "Alolan Meowth"
    # Already handled

    # "Persian Alolan Form" -> "Alolan Persian"
    # Already handled

    # "Weezing Galarian Form" -> "Galarian Weezing"
    # Already handled

    # "Ponyta Galarian Form" -> "Galarian Ponyta" (not in master? check)
    # "Rapidash Galarian Form" -> "Galarian Rapidash"
    # Already handled

    # Tapu Bulu not in master? Let me check...

    return name


def main():
    master = parse_master("master.csv")
    mine_items = parse_mine("mine.csv")

    # Find matches
    results = []
    unmatched_mine = []

    for norm, original in mine_items:
        if norm in master:
            master_name, unavailable, points = master[norm]
            available = unavailable == 0
            results.append((master_name, original, points, available))
        else:
            unmatched_mine.append((norm, original))

    # Sort results: available first, then by points descending
    available_both = [(name, orig, pts) for name, orig, pts, avail in results if avail]
    unavailable = [(name, orig, pts) for name, orig, pts, avail in results if not avail]

    available_both.sort(key=lambda x: (-x[2], x[0]))
    unavailable.sort(key=lambda x: (-x[2], x[0]))

    print("=" * 70)
    print(f"AVAILABLE IN BOTH FILES ({len(available_both)} items)")
    print("=" * 70)
    print(f"{'Master Name':<35} {'Points':>6}")
    print("-" * 42)
    for name, orig, pts in available_both:
        print(f"{name:<35} {pts:>6}")

    print()
    print("=" * 70)
    print(f"IN BOTH FILES BUT UNAVAILABLE ({len(unavailable)} items)")
    print("=" * 70)
    print(f"{'Master Name':<35} {'Points':>6}")
    print("-" * 42)
    for name, orig, pts in unavailable:
        print(f"{name:<35} {pts:>6}")

    if unmatched_mine:
        print()
        print("=" * 70)
        print(f"IN MINE.CSV BUT NO MATCH IN MASTER ({len(unmatched_mine)} items)")
        print("=" * 70)
        for norm, orig in sorted(unmatched_mine):
            print(f"  {orig:<40} (normalized: {norm})")


if __name__ == "__main__":
    main()
