import os

INPUT_FILE = os.path.join(os.path.dirname(__file__), '../data/pospoint.txt')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '../data/pospoint_clean.txt')

def clean_pospoints(input_path, output_path):
    seen = set()
    cleaned_lines = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(';')
            if len(parts) != 3:
                continue
            x, y, raw_name = parts
            station_name = raw_name.replace('@', ' ')
            if station_name not in seen:
                seen.add(station_name)
                cleaned_lines.append(line)
    with open(output_path, 'w', encoding='utf-8') as f:
        for l in cleaned_lines:
            f.write(l + '\n')

if __name__ == '__main__':
    clean_pospoints(INPUT_FILE, OUTPUT_FILE)
    # print(f"Nettoyage terminé. {len(cleaned_lines)} lignes écrites dans {OUTPUT_FILE}") 