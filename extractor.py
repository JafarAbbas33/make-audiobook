import pypandoc
from pathlib import Path

from pdfminer.high_level import extract_text

def book_to_text_file(book_file):
    txt_path = Path(book_file).with_suffix(".txt")

    if book_file.endswith('.txt'):
        print('File is already in text form.')
    elif book_file.endswith('.pdf'):
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
    book_to_text_file('PATH_TO_BOOK')
    print('Conversion completed!')