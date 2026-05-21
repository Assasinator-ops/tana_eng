import re
import csv

INPUT_FILE = "discount.sql"
OUTPUT_FILE = "discount_fixed.sql"
LOG_FILE = "discount_changes.log"

# Correct column order
columns = [
    "id",
    "time",
    "discount_type",
    "discount_money",
    "description",
    "description2",
    "contract_id",
    "carry"
]

# Columns that may be missing
optional_columns = {"time"}

# Word-number mapping
word_to_int = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10
}

def split_values(val_str):
    """Split values while respecting quoted commas."""
    return next(csv.reader([val_str], skipinitialspace=True))

def parse_insert(sql_line):
    """Extract values from INSERT INTO ... VALUES (...)."""
    inside = re.search(r"\((.*)\)", sql_line, re.DOTALL).group(1)
    return split_values(inside)

def convert_word_numbers(value):
    """Convert 'one', 'two', 'three' into integers, remove quotes."""
    val = value.strip().strip("'").strip('"').lower()
    if val in word_to_int:
        return str(word_to_int[val])
    return value

def fix_datatype(col_name, value):
    """Fix value datatype where possible (only safe conversions)."""
    value_stripped = value.strip().strip("'").strip('"')

    # INTEGER FIELDS
    if col_name in ["id", "discount_type", "contract_id"]:
        if value_stripped.isdigit():
            return value_stripped
        return convert_word_numbers(value)

    # FLOAT FIELD
    if col_name == "discount_money":
        try:
            float(value_stripped)
            return value_stripped
        except:
            return convert_word_numbers(value)

    # TEXT FIELDS
    return value  # leave untouched

# Read file
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    content = f.read()

fixed_lines = []
changes = []

for match in re.finditer(r"INSERT INTO\s+`discount`.*?;", content, re.DOTALL):
    original_stmt = match.group(0)
    values = parse_insert(original_stmt)

    col_values = {}

    # Map given values to columns (in order)
    for i, v in enumerate(values):
        if i < len(columns):
            col_values[columns[i]] = v

    # Fill OPTIONAL DEFAULT columns
    for col in optional_columns:
        if col not in col_values:
            col_values[col] = "DEFAULT"

    # Fix datatype issues
    for col in columns:
        if col in col_values and col_values[col] != "DEFAULT":
            old_val = col_values[col]
            new_val = fix_datatype(col, old_val)
            col_values[col] = new_val
            if old_val != new_val:
                changes.append(f"{col}: {old_val} → {new_val}")

    # Build corrected ordered values
    ordered_values = []
    for col in columns:
        ordered_values.append(col_values.get(col, "NULL"))

    new_stmt = (
        "INSERT INTO `discount` ("
        + ", ".join(columns)
        + ") VALUES ("
        + ", ".join(ordered_values)
        + ");"
    )

    fixed_lines.append(new_stmt)

# Write corrected SQL
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(fixed_lines))

# Write change log
with open(LOG_FILE, "w", encoding="utf-8") as f:
    for c in changes:
        f.write(c + "\n")

print("✔ discount_fixed.sql generated")
print("✔ discount_changes.log generated")
print("✔ All INSERT statements normalized successfully")
