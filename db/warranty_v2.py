import re
from pathlib import Path

# Input and output files
INPUT_FILE = "warranty_fixed.sql"
OUTPUT_FILE = "warranty_individual.sql"

def split_insert_line(line):
    """
    Split a multi-row INSERT INTO statement into individual inserts.
    """
    # Extract everything inside VALUES (...)
    values_match = re.search(r"INSERT\s+INTO\s+`warranty`\s+VALUES\s*(.+);", line, re.DOTALL | re.IGNORECASE)
    if not values_match:
        return [line]  # return unchanged if no match

    all_values = values_match.group(1)

    # Split groups like (...),(...) respecting nested parentheses
    # This regex finds each group starting with '(' and ending with ')'
    groups = re.findall(r"\([^\(\)]*\)", all_values)

    individual_inserts = []
    for g in groups:
        new_insert = f"INSERT INTO `warranty` VALUES {g};"
        individual_inserts.append(new_insert)

    return individual_inserts

def main():
    inp_path = Path(INPUT_FILE)
    if not inp_path.exists():
        print(f"Input file {INPUT_FILE} not found.")
        return

    content = inp_path.read_text(encoding="utf-8")

    output_lines = []

    # Process all INSERT INTO warranty lines
    insert_lines = re.findall(r"INSERT\s+INTO\s+`warranty`.*?;", content, re.DOTALL | re.IGNORECASE)
    for line in insert_lines:
        output_lines.extend(split_insert_line(line))

    # Write output
    Path(OUTPUT_FILE).write_text("\n".join(output_lines), encoding="utf-8")
    print(f"✔ Individual inserts saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
