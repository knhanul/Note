from pathlib import Path

text = Path('qml/Main.qml').read_text(encoding='utf-8')
depth = 0
line_num = 1
zero_lines = []

for ch in text:
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
    if ch == '\n':
        if depth == 0:
            zero_lines.append(line_num)
        line_num += 1

print('final depth', depth)
print('zero depth lines (before EOF):', zero_lines[:-1])
