"""Quick sanity check on the draft spec files. Run from /home/claude/."""
import json
import re

ASVS_PATTERN = re.compile(r"^v\d+\.\d+\.\d+-\d+\.\d+\.\d+$")
MASVS_PATTERN = re.compile(r"^MASVS-[A-Z]+-\d+$")

with open("/mnt/user-data/uploads/draft-owasp-asvs.json") as f:
    asvs = json.load(f)
with open("/mnt/user-data/uploads/draft-owasp-masvs.json") as f:
    masvs = json.load(f)

print("=== ASVS ===")
print(f"  spec_version: {asvs['spec_version']}")
print(f"  release_date: {asvs['spec_release_date']}")
print(f"  verified_at:  {asvs['verified_at']}")
print(f"  category count: {len(asvs['categories'])}")
print(f"  chapters: {sorted(asvs['categories'].keys(), key=int)}")
print()

print("=== MASVS ===")
print(f"  spec_version: {masvs['spec_version']}")
print(f"  release_date: {masvs['spec_release_date']}")
print(f"  verified_at:  {masvs['verified_at']}")
print(f"  category count: {len(masvs['categories'])}")
print(f"  control groups: {list(masvs['categories'].keys())}")
print()

print("=== ID format patterns (regex; will live in roadmap_schema.py) ===")
print(f"  ASVS:  {ASVS_PATTERN.pattern}")
print(f"  MASVS: {MASVS_PATTERN.pattern}")
print()

print("=== Example IDs ===")
asvs_examples = [
    "v5.0.0-1.2.5",       # OWASP-recommended example
    "v5.0.0-14.2.1",       # Data Protection
    "v5.0.0-17.1.1",       # WebRTC TURN Server (new in 5.0)
    "v5.0.1-1.2.5",        # Future patch release
]
masvs_examples = [
    "MASVS-STORAGE-1",
    "MASVS-PRIVACY-3",     # New category in 2.1.0
]
old_format_examples = [
    "ASVS V5.1.3",         # 4.0.3 form — should now be REJECTED
    "ASVS V14.2.1",
]

for sample in asvs_examples:
    ok = bool(ASVS_PATTERN.match(sample))
    print(f"  {sample!r:30s} ASVS pattern match: {ok}")
for sample in masvs_examples:
    ok = bool(MASVS_PATTERN.match(sample))
    print(f"  {sample!r:30s} MASVS pattern match: {ok}")
print()
print("=== Old 4.0.3 format (should NOT match new ASVS pattern) ===")
for sample in old_format_examples:
    ok = bool(ASVS_PATTERN.match(sample))
    print(f"  {sample!r:30s} ASVS pattern match: {ok}  (expected: False)")
print()

# Demonstrate version extraction from a 5.0 ID
print("=== Version extraction from ID ===")
for sample in asvs_examples:
    m = re.match(r"^v(?P<version>\d+\.\d+\.\d+)-(?P<chapter>\d+)\.(?P<section>\d+)\.(?P<requirement>\d+)$", sample)
    if m:
        v = m.group("version")
        ch = m.group("chapter")
        chapter_title = asvs["categories"].get(ch, {}).get("title", "<unknown>")
        version_match = (v == asvs["spec_version"])
        print(f"  {sample}: version={v} chapter={ch} ({chapter_title}); matches pinned spec_version: {version_match}")
