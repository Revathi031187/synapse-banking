"""One-off: fix BankingAgentC unified section structure."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "frontend" / "src" / "pages" / "banking" / "BankingAgentC.tsx"
text = p.read_text(encoding="utf-8")

orphan_start = "          {/* Customer mode: one-best-offer card (inside same section) */}\n"
orphan_end = "        </AnimatePresence>\n"

i0 = text.find(orphan_start)
if i0 == -1:
    raise SystemExit("orphan_start not found")
i1 = text.find(orphan_end, i0)
if i1 == -1:
    raise SystemExit("orphan_end not found")
i1 += len(orphan_end)

orphan_block = text[i0:i1]
# Strip comment + offerScope line; keep from AnimatePresence
lines = orphan_block.splitlines(keepends=True)
ap_idx = next(i for i, L in enumerate(lines) if "<AnimatePresence" in L)
inner = lines[ap_idx:]  # AnimatePresence ... through </AnimatePresence>
# Reindent: add 4 spaces to each line (nest under customer fragment)
fixed_inner = []
for L in inner:
    if L.strip() == "":
        fixed_inner.append(L)
    else:
        fixed_inner.append("    " + L)

insert_block = (
    '                <div className="mt-6">\n'
    + "".join(fixed_inner)
    + "                </div>\n"
)

marker = (
    "                  ))}\n"
    "                </div>\n"
    "              </>\n"
    "            )}\n\n"
    "            {offerScope === 'persona' && customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0 && ("
)
if marker not in text:
    raise SystemExit("insert marker not found")
new_after = (
    "                  ))}\n"
    "                </div>\n"
    + insert_block
    + "              </>\n"
    "            )}\n\n"
    "            {offerScope === 'persona' && customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0 && ("
)
text = text.replace(marker, new_after, 1)

# Remove orphan block (re-find after replace shifts)
i0 = text.find(orphan_start)
if i0 == -1:
    raise SystemExit("orphan_start not found after insert")
i1 = text.find(orphan_end, i0)
if i1 == -1:
    raise SystemExit("orphan_end not found after insert")
i1 += len(orphan_end)
# Remove optional following `          {offerScope === 'customer' && (\n` line if still there
text = text[:i0] + text[i1:]
# Remove stray `          {offerScope === 'customer' && (\n` if left
text = text.replace(
    "          {offerScope === 'customer' && (\n        <AnimatePresence mode=\"wait\">\n",
    "",
    1,
)

# Remove duplicate persona sections
dup_start = "        {/* Persona-level churn rollup */}\n"
dup_end = "        {/* Churn cohort */}\n"
ds = text.find(dup_start)
de = text.find(dup_end)
if ds == -1 or de == -1 or de <= ds:
    raise SystemExit(f"dup markers {ds} {de}")
text = text[:ds] + text[de:]

# After persona empty message, ensure we close p-6 then motion.section before Churn cohort
# Pattern: persona msg closes, then `          </div>` should precede churn - insert </motion.section> if missing
churn = "        {/* Churn cohort */}\n"
if text.find(churn) == -1:
    raise SystemExit("churn comment missing")
before_churn = text.split(churn)[0]
if "</motion.section>" not in before_churn.split("Churn cohort")[0] and before_churn.rstrip().endswith("</div>"):
    # Insert </motion.section> right before Churn cohort comment
    text = text.replace(churn, "        </motion.section>\n\n" + churn, 1)

p.write_text(text, encoding="utf-8")
print("OK", p)
