import fitz

doc = fitz.open('NVIDIAAn (1).pdf')
text = ''.join([page.get_text() for page in doc])
print('Blackwell found:', 'Blackwell' in text)
print('Count:', text.count('Blackwell'))

# Find context around Blackwell
if 'Blackwell' in text:
    idx = text.find('Blackwell')
    print('\nContext:')
    print(text[max(0, idx-200):idx+200])
