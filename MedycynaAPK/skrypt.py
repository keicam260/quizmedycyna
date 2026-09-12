import json
import os
import re


def parsuj_pytania(tekst):
    odpowiedzi = {}
    for match in re.finditer(r'^(\d+)\s*\n([A-E])\.', tekst, re.MULTILINE):
        nr = int(match.group(1))
        odpowiedzi[nr] = ord(match.group(2)) - ord('A')

    pytania = []
    iter_pytan = list(re.finditer(r'^(\d+)\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])', tekst, re.MULTILINE))

    for i in range(len(iter_pytan)):
        start_idx = iter_pytan[i].start()
        end_idx = iter_pytan[i + 1].start() if i + 1 < len(iter_pytan) else len(tekst)
        blok = tekst[start_idx:end_idx]

        match_pyt = re.search(r'^(\d+)\s+(.*?)(?=\n[A-E]\.)', blok, re.MULTILINE | re.DOTALL)
        if not match_pyt:
            continue

        nr = int(match_pyt.group(1))
        tresc = match_pyt.group(2).replace('\n', ' ').strip()

        opcje = []
        for litera in ['A', 'B', 'C', 'D', 'E']:
            wzorzec = rf'^{litera}\.?\s*(.*?)(?=\n[A-E]\.|\Z)'
            match_opcja = re.search(wzorzec, blok, re.MULTILINE | re.DOTALL)
            if match_opcja:
                opcje.append(f"{litera}. " + match_opcja.group(1).replace('\n', ' ').strip())

        if len(opcje) >= 2:
            poprawna = odpowiedzi.get(nr, 0)
            if poprawna >= len(opcje):
                poprawna = len(opcje) - 1
            pytania.append({"question": tresc, "options": opcje, "answer": poprawna})

    return pytania


def znajdz_zamykajacy(tekst, indeks_otwarcia, znak_otwierajacy, znak_zamykajacy):
    poziom = 0
    w_cytacie = None
    escape = False

    for i in range(indeks_otwarcia, len(tekst)):
        ch = tekst[i]

        if w_cytacie:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == w_cytacie:
                w_cytacie = None
            continue

        if ch in ('"', "'"):
            w_cytacie = ch
        elif ch == znak_otwierajacy:
            poziom += 1
        elif ch == znak_zamykajacy:
            poziom -= 1
            if poziom == 0:
                return i

    raise ValueError(f"Nie znaleziono zamykającego znaku {znak_zamykajacy}.")


def dodaj_do_zestawu(plik_js, nazwa_zestawu, nowe_pytania):
    if not nowe_pytania:
        return

    if os.path.exists(plik_js):
        with open(plik_js, 'r', encoding='utf-8') as f:
            tekst = f.read()
    else:
        tekst = ""

    payload = json.dumps(nowe_pytania, ensure_ascii=False, indent=4)

    if 'const quizSets' not in tekst:
        nowy_tekst = (
            "const quizSets = {\n"
            f"    {nazwa_zestawu}: {payload}\n"
            "};\n"
        )
        with open(plik_js, 'w', encoding='utf-8') as f:
            f.write(nowy_tekst)
        return

    nazwa_marker = f"{nazwa_zestawu}:"
    pozycja = tekst.find(nazwa_marker)

    if pozycja != -1:
        start_tablicy = tekst.find('[', pozycja)
        if start_tablicy == -1:
            raise ValueError(f"Nie znaleziono tablicy dla zestawu '{nazwa_zestawu}'.")
        koniec_tablicy = znajdz_zamykajacy(tekst, start_tablicy, '[', ']')
        wew = tekst[start_tablicy + 1:koniec_tablicy]
        nowe_elementy = payload[1:-1].strip()
        if wew.strip():
            nowy_wew = wew.rstrip() + ",\n" + nowe_elementy
        else:
            nowy_wew = nowe_elementy
        nowy_tekst = tekst[:start_tablicy + 1] + "\n" + nowy_wew + "\n" + tekst[koniec_tablicy:]
        with open(plik_js, 'w', encoding='utf-8') as f:
            f.write(nowy_tekst)
        return

    quiz_start = tekst.find('const quizSets = {')
    if quiz_start == -1:
        raise ValueError("Nie znaleziono obiektu quizSets.")
    obj_start = tekst.find('{', quiz_start)
    obj_end = znajdz_zamykajacy(tekst, obj_start, '{', '}')
    prev = tekst[:obj_end].rstrip()
    if prev and not prev.endswith(','):
        prev = prev + ','
    nowy_tekst = (
        prev + "\n"
        f"    {nazwa_zestawu}: {payload}\n"
        + tekst[obj_end:]
    )
    with open(plik_js, 'w', encoding='utf-8') as f:
        f.write(nowy_tekst)


def parser_quizu(plik_wejsciowy, plik_wyjsciowy, nazwa_zestawu='miednicaIKrocze'):
    with open(plik_wejsciowy, 'r', encoding='utf-8') as f:
        tekst = f.read()

    pytania = parsuj_pytania(tekst)
    if not pytania:
        print(f"Brak pytań do dodania z pliku {plik_wejsciowy}.")
        return

    dodaj_do_zestawu(plik_wyjsciowy, nazwa_zestawu, pytania)
    print(f"Sukces! Dodano {len(pytania)} pytań do zestawu '{nazwa_zestawu}' w {plik_wyjsciowy}.")


if __name__ == "__main__":
    parser_quizu('dane.txt', 'pytania.js', 'miednicaIKrocze')