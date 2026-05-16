path = r'e:\Pjt\Note2\qml\Main.qml'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

depth = 0
for i in range(20):
    line = lines[i]
    open_count = line.count('{')
    close_count = line.count('}')
    depth += open_count - close_count
    print(f'Line {i+1}: depth={depth:+2d} | {line.rstrip()}')
