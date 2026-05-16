path = r'e:\Pjt\Note2\qml\Main.qml'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines, 1):
    open_count = line.count('{')
    close_count = line.count('}')
    depth += open_count - close_count
    if open_count > 0 or close_count > 0:
        print(f"Line {i:4d}: depth={depth:+2d} | {line.rstrip()}")
