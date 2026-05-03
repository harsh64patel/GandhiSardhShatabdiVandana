import re
from collections import Counter, defaultdict

# Config
BOOK_PATH = "d:/Gandhi/SardhShatabdi/book.html"
OUT_PATH = "d:/Gandhi/SardhShatabdi/book.updated.html"
SUBTITLE_ALT_PATH = "d:/Gandhi/SardhShatabdi/subtitle_alternatives.txt"

# Skip list (do not use in subtitles or index)
SKIP_WORDS = {
    "ગાંધીજી", "સાર્ધ", "શતાબ્દી", "સાર્ધ શતાબ્દી", "વંદના", "રમેશ", "ઓઝા", "શતાબ્દી"
}

# Gujarati stopwords - basic list (not exhaustive). Extend as needed.
STOP_WORDS = {
    "અને", "કે", "છે", "હે", "એ", "તે", "આ", "તો", "થી", "માં", "ના", "ની", "પર", "માટે", "અત્યાર", "બધા", "બાબત", "સાથે", "માટે", "વગેરે", "હવે", "અહીં", "બાદ", "જ", "અન્ય", "ઘટ", "જેમ", "એવા", "તેવા", "જ્યારે", "હોય", "હતો", "હતી", "ત્યાં", "તેમ", "હમણાં", "જોઈએ",
    "હું", "મને", "મારી", "મારા", "તમે", "તને", "તેણે", "તેના", "તેનું", "તેની", "આપ", "આપનું", "આપની", "આપને", "આપણે", "અમે", "અમને", "અમારા", "અમારી", "આપણને", "આપણના", "આપણની", "અપે", "આપના", "આપની", "તે", "જૈસે", "કૃપા", "આવવું", "જવું", "હોય", "છે", "કોઈ", "છે", "છે",
    "પણ", "માત્ર", "અત્યે", "અર્થ", "શે", "જો", "જે", "અનેક", "ઘણા", "થોડા", "જ્યારે", "તે સમયે", "પછી", "અહીંથી",
    "એમ", "એવું", "એવી", "એની", "એનો", "એને", "એટલે", "આવશે", "આવે", "આવ્યા", "આવ્યો", "ઉપર", "એમાં", "એના", "એમાં", "તેના", "તો", "પણ", "માટે", "તેવું",
}

# Generic words to avoid in topic extraction (not meaningful themes)
GENERIC_WORDS = {
    "ગરમ", "બાપુજી", "ઇન્ડીયન", "ચમત્કારો", "મોટામાં", "મર્યાદાઓ", "વ્યક્તિત્વ", "ગાંધીયુગ", "વિચિત્ર", "ઓક્ટોબર", "પોલાક", "સંન્યાસી", "પ્રકાશક", "ગોપાલ", "બાપુજી", "જીવનચરિત્ર", "ગાંધીજી", "ગાંધીજીના", "ગાંધીજીને", "ગાંધીજીનું", "ગાંધીજીની"
}

# Utility
GJ_WORD_RE = re.compile(r'[\u0A80-\u0AFF]+')


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_text(html: str) -> str:
    # Replace <br> with spaces, remove tags.
    text = re.sub(r"<br\s*/?>", " ", html)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def extract_words(text: str):
    return [w for w in GJ_WORD_RE.findall(text)]


def extract_first_clause(chapter_html: str) -> str:
    # Pick first sentence/phrase from the first paragraph, usually starts with "૧." etc.
    m = re.search(r"<p>(.*?)</p>", chapter_html, re.DOTALL)
    if not m:
        return ""
    ptext = m.group(1)
    # Replace <br> tags with spaces, strip tags.
    ptext = re.sub(r"<br\s*/?>", " ", ptext)
    ptext = re.sub(r"<[^>]+>", "", ptext)
    ptext = normalize_whitespace(ptext)
    # Remove leading numbering like '૧.' '૧' etc.
    ptext = re.sub(r"^\s*\d+\s*[\.|\)]?\s*", "", ptext)
    # Take first sentence (split by typical sentence-ending punctuation)
    sentence = re.split(r"[।.!?;]+", ptext, 1)[0]
    words = sentence.split()
    return " ".join(words[:10])


def choose_subtitle(chapter_num: int, top_words: list[str], chapter_html: str) -> str:
    # Chapter 1 uses a special subtitle.
    if chapter_num == 1:
        return "પ્રસ્તાવના : લેખમાળાનો હેતુ અને રચના"

    prefixes = ["વિચાર", "પ્રસંગ", "પ્રેરણા"]
    prefix = prefixes[(chapter_num - 2) % len(prefixes)]

    # Use the most frequent meaningful words as a high-level theme summary.
    if top_words:
        w1 = top_words[0]
        w2 = top_words[1] if len(top_words) > 1 else None
        if w2:
            return f"{prefix} : {w1} અને {w2}"
        return f"{prefix} : {w1}"

    # Fallback: attempt to use the opening sentence as a short summary.
    first_clause = extract_first_clause(chapter_html)
    if first_clause:
        # Ensure it does not contain skip words
        for w in SKIP_WORDS:
            first_clause = first_clause.replace(w, "")
        first_clause = normalize_whitespace(first_clause)
        if first_clause:
            words = first_clause.split()
            if len(words) >= 5:
                return f"{prefix} : {' '.join(words[:10])}"

    return f"{prefix} : વિચાર"  # fallback


def subtitle_alternatives(chapter_num: int, top_words: list[str], chapter_html: str) -> list[str]:
    if chapter_num == 1:
        return [
            "પ્રસ્તાવના : લેખમાળાનો હેતુ અને રચના",
            "પ્રસ્તાવના : સત્ય અને ગતિમાં અમર યાત્રા",
            "પુસ્તકની યાત્રા માટેની પરિચય રેખા",
        ]

    prefixes = ["વિચાર", "પ્રસંગ", "પ્રેરણા"]
    prefix = prefixes[(chapter_num - 2) % len(prefixes)]

    first_clause = extract_first_clause(chapter_html)
    alts = []
    if first_clause:
        words = first_clause.split()
        if len(words) >= 5:
            short = " ".join(words[:10])
            alts.extend([
                f"{prefix} : {short}",
                f"{prefix} : {short} પર",
                f"{prefix} : {short} વિશે",
            ])

    if top_words:
        w1 = top_words[0]
        w2 = top_words[1] if len(top_words) > 1 else None
        alts.append(f"{prefix} : {w1}")
        if w2:
            alts.append(f"{prefix} : {w1} અને {w2} પર")
        else:
            alts.append(f"{prefix} : {w1} વિશે")

    # Remove duplicates while preserving order
    seen = set()
    cleaned = []
    for alt in alts:
        if alt not in seen:
            seen.add(alt)
            cleaned.append(alt)

    return cleaned[:5]


def filter_word(word: str) -> bool:
    if word in SKIP_WORDS or word in STOP_WORDS:
        return False
    if len(word) <= 1:
        return False
    # Do not include purely digits
    if word.isdigit():
        return False
    return True


def generate_index(keywords_map: dict[str, set[int]]) -> str:
    # Sort keywords alphabetically (unicode order). Use stable sorting.
    entries = []
    for kw in sorted(keywords_map.keys(), key=lambda s: s.lower()):
        chapters = sorted(keywords_map[kw])
        links = ", ".join(f"<a href='#chapter{c}'>{c}</a>" for c in chapters)
        entries.append(f"<div class='index-entry'><a href='#chapter{chapters[0]}'>{kw}</a>, {links}</div>")
    return "\n".join(entries)


def main():
    with open(BOOK_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # Split document to isolate index section.
    idx_split = re.split(r"(<h2 class='toc-title'>અનુક્રમ</h2>\s*<div class='index'>)", html)
    if len(idx_split) < 3:
        raise SystemExit("Could not find index section")
    before_index = idx_split[0]
    index_header = idx_split[1]
    after_index = idx_split[2]

    # We'll rebuild index later.

    # Find all chapter sections
    chapter_pattern = re.compile(r"(<div class='chapter' id='chapter(\d+)'>)(.*?)(?=<div class='chapter' id='chapter\d+'|$)", re.DOTALL)
    chapters = list(chapter_pattern.finditer(before_index))

    # mappings
    chapter_html_map = {}
    chapter_freqs = {}
    overall_freq = Counter()

    # First pass: gather word frequencies for each chapter and overall
    for ch in chapters:
        chapter_html = ch.group(0)
        chap_num = int(ch.group(2))
        chapter_html_map[chap_num] = chapter_html

        # Extract plain text from chapter
        plain = extract_text(chapter_html)
        words = [w for w in extract_words(plain) if filter_word(w)]
        freq = Counter(words)
        chapter_freqs[chap_num] = freq
        overall_freq.update(freq)

    # Determine overly common words that should be excluded from the index
    common_threshold = 50
    common_words = {w for w, cnt in overall_freq.items() if cnt > common_threshold}
    STOP_WORDS.update(common_words)

    keywords_map = defaultdict(set)
    subtitle_map = {}
    subtitle_alternatives_map = {}

    # Second pass: pick top keywords per chapter, and build subtitles
    for chap_num, freq in chapter_freqs.items():
        top = [w for w, _ in freq.most_common() if w not in STOP_WORDS and filter_word(w) and w not in GENERIC_WORDS]
        top = top[:5]

        for w in top:
            keywords_map[w].add(chap_num)

        chapter_html = chapter_html_map[chap_num]
        subtitle_map[chap_num] = choose_subtitle(chap_num, top, chapter_html)
        subtitle_alternatives_map[chap_num] = subtitle_alternatives(chap_num, top, chapter_html)

    # Build new index HTML
    filtered_keys = {
        k: v
        for k, v in keywords_map.items()
        if len(v) >= 2 and k not in STOP_WORDS
    }
    index_html = generate_index(filtered_keys)

    # Replace subtitles in the html
    def replace_sub(match):
        chap_id = int(match.group('chap'))
        return f"<div class='chapter-subtitle'>({subtitle_map.get(chap_id, match.group('text'))})</div>"

    # Add named groups to regex for replacement.
    subtitle_pattern = re.compile(r"<div class='chapter-subtitle'>(?P<text>.*?)</div>")
    updated_before_index = chapter_pattern.sub(lambda m: m.group(0).replace(
        re.search(r"<div class='chapter-subtitle'>(.*?)</div>", m.group(0), re.DOTALL).group(0),
        f"<div class='chapter-subtitle'>({subtitle_map[int(m.group(2))]})</div>"
    ), before_index)

    new_html = updated_before_index + index_header + "\n" + index_html + "\n</div>" + after_index

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(new_html)

    # Write subtitle alternatives file
    with open(SUBTITLE_ALT_PATH, 'w', encoding='utf-8') as f:
        for chap in sorted(subtitle_alternatives_map.keys()):
            f.write(f"Chapter {chap}:\n")
            f.write(f"  Selected: {subtitle_map[chap]}\n")
            f.write("  Alternatives:\n")
            for alt in subtitle_alternatives_map[chap]:
                f.write(f"    - {alt}\n")
            f.write("\n")


if __name__ == '__main__':
    main()
