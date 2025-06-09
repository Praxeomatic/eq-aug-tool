import pandas as pd

# Path to your master EverQuest item database file
input_file = "items.txt"   # Replace this with your actual filename if different
output_file = "augmentation_only_items.csv"

# Load the full database (pipe-delimited) and skip malformed lines
print(f"Loading item database from: {input_file}")
df = pd.read_csv(input_file, sep="|", low_memory=False, on_bad_lines="skip")

# Report total item count
print(f"Total items in database: {len(df)}")

# Check required column
if "augtype" not in df.columns:
    raise ValueError("Missing 'augtype' column — cannot filter augmentations.")

# Filter to augs only
aug_df = df[df["augtype"] > 0]
print(f"Augmentations found: {len(aug_df)}")

# Save to CSV
aug_df.to_csv(output_file, index=False)
print(f"✅ Saved augment-only file to: {output_file}")
