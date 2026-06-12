import sys
import json
import montmark


SPEC = 'tests/spec.json'
OK = 'O'
KO = 'K'

def read_cases(filename) -> list:
    with open(filename, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    return cases


def print_case(example, markdown, html, section, test, passed):
    print(f"{passed} = {example:03}", "="*50, section, "="*10, file=sys.stdout)
    print(f"{passed}   {example:03}", "markdown:", repr(markdown), file=sys.stdout)
    print(f"{passed}   {example:03}", "expected:", repr(html), file=sys.stdout)
    print(f"{passed}   {example:03}", "montmark:", repr(test), file=sys.stdout)
    return


def test_case(example, markdown, html, section):
    test = montmark.convert(markdown)
    passed = OK if test == html else KO
    return passed, test


def test_cases(cases: list):
    for case in cases:
        example  = int(case['example'])
        markdown = case['markdown']
        html     = case['html']
        section  = case['section']
        passed, test = test_case(example, markdown, html, section)
        case['passed'] = passed
        case['test'] = test
        print_case(example, markdown, html, section, test, passed)
    return


def make_conclusion(cases: list):
    O = sys.stdout
    E = sys.stderr
    COLXL = 45
    COL = 6
    sections = {}
    order_appearance = []
    total_ok = 0
    total_ko = 0
    for case in cases:
        example  = int(case['example'])
        section  = case['section']
        passed = case['passed']
        if section not in sections:
            sections[section] = {OK: 0, KO: 0, 'bugs':[]}
            order_appearance.append(section)
        sections[section][passed] += 1
        if passed == KO:
            sections[section]['bugs'].append(str(case['example']))
    print("\n")
    print(f"| {'Section':{COLXL}} |{'OK':>{COL}} |{'Total':>{COL}} |{'% OK':>{COL}} | {'Discrepancies':{COLXL}} |", file=E)
    print(f"| {'-' * COLXL} | {'-' * (COL-1)} | {'-' * (COL-1)} | {'-' * (COL-1)} | {'-' * (COLXL)} |", file=E)
    for section in order_appearance:
        nb_ok = sections[section][OK]
        nb_ko = sections[section][KO]
        bugs = sections[section]['bugs']
        total_ok += nb_ok
        total_ko += nb_ko
        percent = nb_ok*100//(nb_ok+nb_ko)
        print(f"| {section:{COLXL}} |{nb_ok:{COL}} |{nb_ok+nb_ko:{COL}} |{percent:{COL-1}}% | {','.join(bugs):{COLXL}} |", file=E)
    percent = total_ok*100//(total_ok+total_ko)
    print(f"| {'ALL':{COLXL}} |{total_ok:{COL}} |{total_ok+total_ko:{COL}} |{percent:{COL-1}}% | {' ' * COLXL} |", file=E)
    return


def main():
    #print(sys.argv)
    cases = read_cases(SPEC)#[:20]
    test_cases(cases)
    make_conclusion(cases)


if __name__ == '__main__':
    main()

