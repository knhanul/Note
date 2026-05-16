with open('qml/Main_backup.qml', 'r', encoding='utf-16') as f:
    lines = f.readlines()

depth = 0
for i in range(0, 20):
    line = lines[i]
    open_count = line.count('{')
    close_count = line.count('}')
    depth += open_count - close_count
    print(f'Line {i+1}: depth={depth:+2d} | {line.rstrip()}')
