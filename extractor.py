#!/usr/bin/env python3

import time
import pypandoc
import pyperclip
from pathlib import Path

from pdfminer.high_level import extract_text

def book_to_text_file():
    txt_path = Path(book_file).with_suffix(".txt")

    if book_file.as_posix().endswith('.txt'):
        print('File is already in text form.')
    elif book_file.as_posix().endswith('.pdf'):
        text = extract_text(book_file)
        with open(txt_path, 'w') as f:
            f.write(text)
    else:
        try:
            pypandoc.convert_file(book_file, "plain", outputfile=txt_path, extra_args=["--wrap=none"])
            return
        except RuntimeError:
            print("Format not recognized. Treating as plain text...")
            with open(book_file) as f:
                text = f.read()
            with open(txt_path, 'w') as f:
                f.write(text)

if __name__ == '__main__':
    clipboard_data = pyperclip.paste()
    print('Clipboard data:', clipboard_data)
    print('Taking path from clipboard in 4 seconds...')
    time.sleep(4)
    book_file = Path(clipboard_data)
    assert book_file.exists(), 'Path does not exist.'
    assert book_file.is_file(), 'Path is not a file.'
    book_to_text_file()
    print('Conversion completed!')
    print('Exiting in 4 seconds...')
    time.sleep(4)
