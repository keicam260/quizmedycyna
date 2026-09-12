from pathlib import Path
text = Path(r'C:/Users/keica/OneDrive/Dokumenty/MedycynaAPK/pytania.js').read_text(encoding='utf-8')
stack=[]
quote=None
escape=False
for i,ch in enumerate(text):
    if quote:
        if escape:
            escape=False
        elif ch == '\\':
            escape=True
        elif ch == quote:
            quote=None
        continue
    if ch in ('"', "'"):
        quote = ch
    elif ch in '{[(':
        stack.append((ch, i))
    elif ch in '}])':
        if not stack:
            print('UNMATCHED_CLOSE', ch, 'at index', i)
            print(text[max(0, i-200): i+200])
            break
        op, idx = stack.pop()
        pairs = {'{': '}', '[': ']', '(': ')'}
        if pairs[op] != ch:
            print('MISMATCH', op, idx, ch, i)
            print(text[max(0, idx-200): i+200])
            break
else:
    print('OPEN_COUNT', len(stack))
    if stack:
        print('LAST_10', stack[-10:])
        print(text[max(0, stack[-1][1]-200): min(len(text), stack[-1][1]+200)])
