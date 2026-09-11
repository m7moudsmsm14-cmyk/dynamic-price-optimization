"""Create a representative 20,000-row sample from the original retail dataset.

Usage:
    python create_demo_sample.py /path/to/full_dataset.csv

The script reads the large CSV in chunks, counts product frequencies, then takes a
stratified sample by product_id (with a minimum allocation for products that appear
in the data). It keeps the required project columns and writes data/demo_data.csv.
"""
import sys
from pathlib import Path
import pandas as pd

N = 20_000
REQUIRED = ["product_id", "store_id", "date", "price", "sales", "stock", "promo_bin_1"]

if len(sys.argv) < 2:
    raise SystemExit("Usage: python create_demo_sample.py /path/to/full_dataset.csv")

src = Path(sys.argv[1])
out = Path(__file__).parent / "data" / "demo_data.csv"
out.parent.mkdir(parents=True, exist_ok=True)

# Pass 1: collect product counts without loading the full dataset.
counts = {}
for chunk in pd.read_csv(src, usecols=lambda c: c in REQUIRED, chunksize=100_000):
    missing = set(REQUIRED) - set(chunk.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    vc = chunk["product_id"].value_counts()
    for k, v in vc.items():
        counts[k] = counts.get(k, 0) + int(v)

if not counts:
    raise ValueError("No rows were found in the source CSV.")

total = sum(counts.values())
products = list(counts)

# Allocate approximately proportional rows, while giving every product one row
# when possible. This preserves product coverage better than taking the first 20k rows.
alloc = {p: max(1, int(round(N * counts[p] / total))) for p in products}
# Correct rounding to exactly N.
while sum(alloc.values()) > N:
    p = max((p for p in products if alloc[p] > 1), key=lambda x: alloc[x] / counts[x])
    alloc[p] -= 1
while sum(alloc.values()) < N:
    p = max(products, key=lambda x: counts[x] - alloc[x])
    alloc[p] += 1

# Pass 2: reservoir sample inside each product group, so memory stays bounded.
reservoir = {p: [] for p in products}
seen = {p: 0 for p in products}
import random
rng = random.Random(42)

for chunk in pd.read_csv(src, usecols=REQUIRED, chunksize=100_000):
    for product, group in chunk.groupby("product_id", sort=False):
        k = alloc.get(product, 0)
        if k <= 0:
            continue
        bucket = reservoir[product]
        for row in group.itertuples(index=False, name=None):
            seen[product] += 1
            if len(bucket) < k:
                bucket.append(row)
            else:
                j = rng.randrange(seen[product])
                if j < k:
                    bucket[j] = row

rows = [r for bucket in reservoir.values() for r in bucket]
demo = pd.DataFrame(rows, columns=REQUIRED)
demo = demo.sample(frac=1, random_state=42).reset_index(drop=True)
demo.to_csv(out, index=False)

print(f"Created: {out}")
print(f"Rows: {len(demo):,}")
print(f"Products represented: {demo.product_id.nunique():,}")
print(f"Stores represented: {demo.store_id.nunique():,}")
