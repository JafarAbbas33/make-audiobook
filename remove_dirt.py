import re
import string

print()

path = 'PATH_TO_TEXT_FILE' # For .txt file only!!
re_text = rf'Page \d+Goldenagato \| mp4directs.com' # Or use | (Pipe/Or operator) to match more bloat text like: 'a|b' will match either a or b

def fix_sen(sen):
    sen = ''.join(filter(lambda x: x in set(string.printable), sen)) # Get printable text
    sen = re.sub(r"_", " ", sen) # remove _italics_
    sen = re.sub(r"(\-{3,})", "Footnote: ", sen) # remove --- hyphens for footnotes
    sen = sen.replace('\n', ' ').strip() # Replace all new lines with white spaces
    cleaned_text = ' '.join(sen.split()) # Remove all extra white spaces
    return cleaned_text

def main():
    with open(path, encoding="utf-8") as book:
        text = book.read()

    re_fix = re.sub(re_text, '', text)
    fixed_sen = fix_sen(re_fix)

    with open(f"{path.replace('.txt', '')}_fixed.txt", 'w', encoding="utf-8") as book:
        book.write(fixed_sen + '\n')

    print('Done!')


if __name__ == '__main__':
    main()