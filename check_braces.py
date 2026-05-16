path = r'e:\Pjt\Note2\qml\Main.qml'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

depth = 0
line = 1
zeros = []
for i, ch in enumerate(text):
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
    if ch == '\n':
        if depth == 0:
            zeros.append(line)
        line += 1

print(f'final depth={depth}')
print(f'zero depth lines: {zeros}')
