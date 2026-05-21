import re
from pathlib import Path

# Input and output files
INPUT_FILE = "warranty.sql"
OUTPUT_FILE = "warranty_fixed.sql"

def remove_id_prefix(value):
    """Remove leading 'ID' from a string, leave others untouched."""
    v = value.strip().strip("'").strip('"')
    if v.upper().startswith("ID"):
        v = v[2:]  # remove the first two chars
    return f"'{v}'"  # keep single quotes for SQL

def process_insert_line(line):
    """
    Process a single INSERT INTO `warranty` line:
    - Finds all parentheses groups
    - Fix elevator_id (last value) by removing 'ID' prefix
    - Rebuilds the INSERT line
    """
    groups = re.findall(r"\((.*?)\)", line, re.DOTALL)
    new_groups = []

    for g in groups:
        # Split by commas, respecting quoted strings
        parts = re.findall(r"'[^']*'|[^,]+", g)
        parts = [p.strip() for p in parts]

        if len(parts) < 4:
            # malformed row, skip
            new_groups.append(f"({g})")
            continue

        # elevator_id is the last value (index -1)
        parts[-1] = remove_id_prefix(parts[-1])

        # Rebuild the group
        new_group = "(" + ",".join(parts) + ")"
        new_groups.append(new_group)

    # Rebuild the full INSERT statement
    prefix = line[:line.find("(")]
    new_line = prefix + ",".join(new_groups) + ";"
    return new_line

def main():
    inp_path = Path(INPUT_FILE)
    if not inp_path.exists():
        print(f"Input file {INPUT_FILE} not found.")
        return

    content = inp_path.read_text(encoding="utf-8")

    # Process all INSERT INTO warranty lines
    def replacer(match):
        return process_insert_line(match.group(0))

    pattern = r"INSERT\s+INTO\s+`warranty`.*?;"
    fixed_content = re.sub(pattern, replacer, content, flags=re.DOTALL | re.IGNORECASE)

    # Write output
    Path(OUTPUT_FILE).write_text(fixed_content, encoding="utf-8")
    print(f"✔ Fixed SQL saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
