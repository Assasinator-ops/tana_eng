import re

# File to read + write
filename = "contract.sql"

# Number-word mapping (extend if needed)
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

# Regex to find quoted words
pattern = re.compile(r"'(.*?)'")

def convert_word_number(match):
    word = match.group(1).strip().lower()
    if word in word_to_int:
        return str(word_to_int[word])  # return number WITHOUT quotes
    return match.group(0)  # return original quoted value

# Read file
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

# Replace number-words inside quotes
new_content = pattern.sub(convert_word_number, content)

# Write back
with open(filename, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Conversion complete: word-numbers fixed in contract.sql")
