import os
from colorama import Fore
import chardet
import subprocess
import time
import re

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def convert_encoding(file, output, from_encoding, to_encoding):
    try:
        with open(file, 'r', encoding=from_encoding) as infile:
            content = infile.read()
        with open(output, 'w', encoding=to_encoding) as outfile:
            outfile.write(content)
        print(f"Successfully created {output} from {file}")
    except Exception as e:
        print(f"Error converting file encoding: {e}")


#decodes file content from windows-1251 to utf-8 (Cyrillic conversion)
def to_cyrillic(file, output):
    convert_encoding(file, output, 'windows-1251', 'utf-8')


#decodes file content from utf-8 to iso-8859-1 (Latin conversion)
def to_latin(file, output):
    convert_encoding(file, output, 'utf-8', 'iso-8859-1')

def find_diacritics(file):
    diacritic_pattern = re.compile(r'[áéíóúÁÉÍÓÚàèìòùÀÈÌÒÙäëïöüÄËÏÖÜãõÃÕâêîôûÂÊÎÔÛñÑçÇ]')
    print("Looking for suspicious diacritics...")

    try:
        with open(file, encoding='utf-8', errors='replace') as f:
            for line in f:
                if diacritic_pattern.search(line):
                    print(f"\t{Fore.LIGHTYELLOW_EX}✗ Found suspicious diacritics! Decoding...{Fore.RESET}")
                    return True
        print(f"\t{Fore.GREEN} ✔ No suspicious diacritics in {file} {Fore.RESET}")
        return False
    except Exception as e:
        print(f"Error reading the file: {e}")
        return False


def diacritics(file, output):
    print("\tDecoding diacritics...")
    to_latin(file, 'residual.csv')
    if not file_exists('residual.csv'):
        print("Error: residual.csv was not created.")
        return
    to_cyrillic('residual.csv', output)
    print("Deleting residual files...")
    try:
        os.remove('residual.csv')
        print("Successfully deleted residual.csv")
    except OSError as e:
        print(f"Error: {e.strerror}.")

def find_diamonds(file, chunk_size=1024):
    diamond = b'\xef\xbf\xbd'  #byte '�'
    print("Looking for '�'... ")

    try:
        with open(file, 'rb') as f:
            while chunk := f.read(chunk_size):
                if diamond in chunk:
                    print(f"\t{Fore.LIGHTYELLOW_EX}✗ Found a diamond! Decoding...{Fore.RESET}")
                    return True
        print(f"\t{Fore.GREEN}✔ No '�' in {file} {Fore.RESET}")
        return False
    except Exception as e:
        print(f"Error reading the file: {e}")
        return False

def universal_decoding(file, encoding, ext):
    try:
        output = f'{name(file)}_decoded{ext}'
        convert_encoding(file, output, encoding, 'utf-8')
        print(f'Successfully decoded file. Check {output}')
    except Exception as e:
        print(f"Couldn't decode {file}: {e}")

def extension(file):
    return os.path.splitext(file)[1].lower()

def name(file):
    return os.path.splitext(file)[0]


def file_exists(file):
    return os.path.exists(file)


def detect_encoding(file_path):
    try:
        with open(file_path, 'rb') as file:
            detector = chardet.universaldetector.UniversalDetector()

            for _ in range(2500):  # Read up to 2500 lines to detect encoding
                line = file.readline()
                detector.feed(line)
                if detector.done or not line:
                    break

            detector.close()
        encoding = detector.result['encoding']
        print(f"{Fore.CYAN}Detected encoding: {encoding}{Fore.RESET}")
        return encoding
    except Exception as e:
        print(f"Error detecting encoding: {e}")
        return None


def running_parser(file):
    try:
        command = f'python3 "SqlParserPlus.py" -s "{file}"'  # Modify the SqlParser path as needed
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Executing SqlParser+")
            return True
        else:
            print(f"Error occurred:\n{result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Unable to run SqlParserPlus: {e}")
        return False


def csv_check(file, output, encoding, ext):
    if encoding == 'utf-8':
        print('\n')
        print("Decoder encountered some issues...")
        time.sleep(1) 
        print("Trying something else...")

        if find_diamonds(file):
            to_cyrillic(file, output)
        elif find_diacritics(file):
            diacritics(file, output)
    else:
        universal_decoding(file, encoding, ext)

def main_menu():
    while True:
        print('\n')
        raw_file = input(f'{Fore.CYAN}Name of the file: {Fore.RESET}')
        ext = extension(raw_file)
        n = name(raw_file)

        if file_exists(raw_file):
            time.sleep(1)
            print("Finding the file's encoding...")
            encoding = detect_encoding(raw_file)
            print('\n')
            print("\t1. Cyrillic")
            print("\t2. Detect encoding")
            print('\n')
            choice = int(input(f'{Fore.CYAN}Enter your choice: {Fore.RESET}'))
            output = f'{n}_decoded{ext}'

            

            match choice:
                case 1:
                    print("You entered: Cyrillic")
                    match ext:
                        case '.sql':
                            print("Decoding your file...")
                            universal_decoding(raw_file, encoding, ext)
                            running_parser(output)
                        case '.csv':
                            csv_check(raw_file, output, encoding, ext)
                        case '.txt':
                            print("Converting .txt to .csv")
                            csv_output = f'{n}.csv'
                            command = f'iconv -f {encoding} -t {encoding} {raw_file} -o {csv_output}'
                            subprocess.run(command, shell=True, capture_output=True, text=True)

                            if file_exists(csv_output):
                                print(f"Successfully converted {raw_file} to {csv_output}")
                                csv_check(csv_output, f'{n}_decoded.csv', encoding, '.csv')
                            else:
                                print("Something went wrong while converting the file. Please change .txt to .csv manually.")
                case 2:
                    print(f"Detected encoding: {detect_encoding(raw_file)}")
        else:
            print(f"{Fore.RED}The file doesn't exist in the directory!{Fore.RESET}")

if __name__ == "__main__":
    
    print("""\
        
        
            W E L C O M E                              TO      
░░░░       ░░░        ░░░      ░░░░      ░░░       ░░░        ░░       ░░░░░░
▒▒▒▒  ▒▒▒▒  ▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒  ▒▒  ▒▒▒▒  ▒▒  ▒▒▒▒  ▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒  ▒▒▒▒▒
▓▓▓▓  ▓▓▓▓  ▓▓      ▓▓▓▓  ▓▓▓▓▓▓▓▓  ▓▓▓▓  ▓▓  ▓▓▓▓  ▓▓      ▓▓▓▓       ▓▓▓▓▓▓
████  ████  ██  ████████  ████  ██  ████  ██  ████  ██  ████████  ███  ██████
████       ███        ███      ████      ███       ███        ██  ████  █████

                    ___.___    ~            _____________
                    \  \\  \   ,, ???      |        '\\\\\\
                    \  \\  \ /<   ?       |        ' ____|_
                    --\//,- \_.  /_____  |        '||::::::
                        o- /   \_/    '\ |        '||_____|
                        | \ '   o       \'________|_____|
                        |  )-   #     <  ___/____|___\___
                        `_/'------------|    _    '  <<<:|
                            /________\| |_________'___o_o|
                                                            
                                                                                
            """)
    print("✭ Tip: If you're having trouble with csv files please input the original file \n it has been converted from")
    print("✭ This tool is still a work in progress, please have SqlParser+ and Decoder \n in the directory you're working.")
    print("✭ I want to make the app as convenient as possible, please give me feedback\n and send me a detailed description of the issues you encounter!")
    main_menu()