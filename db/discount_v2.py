import re
import csv
from pathlib import Path

INPUT_FILE = "discount.sql"
OUTPUT_FILE = "discount_fixed.sql"
LOG_FILE = "discount_changes.log"

# Target columns (time removed)
COLUMNS = [
    "id",
    "discount_type",
    "discount_money",
    "description",
    "description2",
    "contract_id"
]

# mapping for word-numbers
WORD_TO_INT = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

# helpers --------------------------------------------------------------------

def split_group_values(group_text):
    """
    Given the inner text of a single parentheses group (no surrounding parens),
    returns a list of raw value tokens preserving quoted commas.
    """
    # csv.reader respects quotes and commas inside quotes
    return next(csv.reader([group_text], skipinitialspace=True))

def strip_quotes(v):
    v = v.strip()
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        return v[1:-1]
    return v

def is_integer_str(s):
    s = s.strip().strip("'").strip('"')
    return re.fullmatch(r"-?\d+", s) is not None

def is_float_str(s):
    s = s.strip().strip("'").strip('"')
    return re.fullmatch(r"-?\d+(\.\d+)?", s) is not None

def word_number_to_int_token(token):
    """
    If token represents a word like 'one', return numeric token (no quotes).
    Otherwise return None.
    """
    raw = strip_quotes(token).strip().lower()
    if raw in WORD_TO_INT:
        return str(WORD_TO_INT[raw])
    return None

def safe_sql_string(s):
    """Return a single-quoted SQL-safe string: escape internal single quotes by doubling them."""
    if s is None:
        return "''"
    return "'" + s.replace("'", "''") + "'"

def normalize_text_token(token):
    """Ensure token is SQL single-quoted text, escaping properly."""
    # If token is literal NULL (case-insensitive), return NULL (no quotes)
    if token.strip().lower() == "null":
        return "NULL"
    inner = strip_quotes(token)
    return safe_sql_string(inner)

def normalize_int_token(col_name, token):
    """Return an integer token (no quotes) or NULL if cannot convert."""
    # First try digit
    t = token.strip()
    # convert word numbers
    wn = word_number_to_int_token(t)
    if wn is not None:
        return wn
    # remove quotes if present
    t2 = strip_quotes(t)
    if re.fullmatch(r"-?\d+", t2):
        return t2
    # fallback: NULL (log later)
    return "NULL"

def normalize_float_token(token):
    """Return float token (no quotes) or NULL if cannot convert."""
    t = token.strip()
    # word-number conversion may be meaningful for floats too
    wn = word_number_to_int_token(t)
    if wn is not None:
        return wn
    t2 = strip_quotes(t)
    # Accept integers and floats
    if re.fullmatch(r"-?\d+(\.\d+)?", t2):
        return t2
    return "NULL"

# core processing ------------------------------------------------------------

def extract_insert_blocks(sql_text):
    """
    Return list of full INSERT ...; blocks that target `discount`.
    This captures up to the terminating semicolon.
    """
    pattern = r"INSERT\s+INTO\s+`discount`[^;]*;"
    return [m.group(0) for m in re.finditer(pattern, sql_text, flags=re.IGNORECASE | re.DOTALL)]

def extract_parenthesis_groups(block):
    """
    Return list of inner-texts of each (...) group inside the VALUES clause.
    e.g. "(11,0,'one',...),(12,0,'one',...)" -> list of strings without outer parens.
    """
    # find the VALUES keyword and then capture all (...) groups after it
    # NOTE: this simple approach assumes parentheses used here correspond to value tuples
    groups = re.findall(r"\((.*?)\)", block, flags=re.DOTALL)
    return groups

def process_group_text(group_text, change_log, block_index, row_index):
    """
    Process a single tuple group text and return a cleaned list of tokens
    matching COLUMNS order (after removing time).
    """
    raw_vals = split_group_values(group_text)  # respects quoted commas
    # Defensive: strip whitespace around tokens
    raw_vals = [v.strip() for v in raw_vals]

    # Old format assumed: (id, time, discount_type, discount_money, description, description2, contract_id[, carry])
    # Remove the time value at index 1 if present
    if len(raw_vals) >= 2:
        removed_time = raw_vals.pop(1)
        change_log.append(f"block{block_index}_row{row_index}: removed time value -> {removed_time}")

    # Now raw_vals corresponds to (id, discount_type, discount_money, description, description2, contract_id[, carry])
    # Ensure we have enough tokens: if carry missing, append empty string '' as carry
    expected_len = len(COLUMNS)
    if len(raw_vals) < expected_len:
        missing = expected_len - len(raw_vals)
        # Append empty strings for missing trailing text-like columns (carry)
        for _ in range(missing):
            raw_vals.append("''")
        change_log.append(f"block{block_index}_row{row_index}: appended {missing} missing carry/text placeholders")

    # Map & normalize per column
    normalized = {}
    for col, token in zip(COLUMNS, raw_vals):
        if col in ("id", "discount_type", "contract_id"):
            new_tok = normalize_int_token(col, token)
            if new_tok != token.strip().strip("'").strip('"'):
                change_log.append(f"block{block_index}_row{row_index}: {col} {token} -> {new_tok}")
            normalized[col] = new_tok
        elif col == "discount_money":
            new_tok = normalize_float_token(token)
            if new_tok != token.strip().strip("'").strip('"'):
                change_log.append(f"block{block_index}_row{row_index}: {col} {token} -> {new_tok}")
            normalized[col] = new_tok
        else:
            # text fields: description, description2, carry
            # ensure quoted and escape inner quotes
            # If token is NULL literal, keep NULL
            t_trim = token.strip()
            if t_trim.lower() == "null":
                normalized[col] = "NULL"
            else:
                inner = strip_quotes(token)
                normalized[col] = safe_sql_string(inner)
                if token != normalized[col]:
                    change_log.append(f"block{block_index}_row{row_index}: {col} normalized to quoted string")

    # final order list
    ordered = [normalized[c] for c in COLUMNS]
    return ordered

def build_single_insert_statement(ordered_values):
    """
    Build an explicit INSERT with backtick columns and the provided ordered_values tokens.
    """
    col_list = ",".join(f"`{c}`" for c in COLUMNS)
    val_list = ", ".join(ordered_values)
    return f"INSERT INTO `discount` ({col_list}) VALUES ({val_list});"

# run ------------------------------------------------------------------------

def main():
    inp = Path(INPUT_FILE)
    if not inp.exists():
        print(f"Input file '{INPUT_FILE}' not found.")
        return

    sql_text = inp.read_text(encoding="utf-8")
    blocks = extract_insert_blocks(sql_text)
    if not blocks:
        print("No INSERT INTO `discount` blocks found.")
        return

    all_out_lines = []
    change_log = []

    for b_idx, block in enumerate(blocks, start=1):
        groups = extract_parenthesis_groups(block)
        for r_idx, group in enumerate(groups, start=1):
            ordered = process_group_text(group, change_log, b_idx, r_idx)
            stmt = build_single_insert_statement(ordered)
            all_out_lines.append(stmt)

    # write outputs
    Path(OUTPUT_FILE).write_text("\n".join(all_out_lines) + "\n", encoding="utf-8")
    Path(LOG_FILE).write_text("\n".join(change_log) + "\n", encoding="utf-8")

    print(f"Processed {len(all_out_lines)} rows from {len(blocks)} insert block(s).")
    print(f"Wrote corrected SQL to: {OUTPUT_FILE}")
    print(f"Wrote change log to: {LOG_FILE}")

if __name__ == "__main__":
    main()
