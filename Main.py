import json
import csv
import re

# Path to your JSON file and the desired output CSV
input_json = "Sticker priya 03-01-2025 - Sheet2.json"
output_csv = "output.csv"

# Define the columns in the desired order. The two columns "Nutrient" and "Quantity"
# will be populated per nutrient row, while the rest come from the product data.
COLUMN_MAPPING = [
    ("Product Name",               "Product Name"),
    ("Label Format",               "Label Format"),
    ("SKU",                        "SKU"),
    ("Product ID",                 "Product ID"),
    ("Size",                       "Size"),
    ("#servper_Cont",             "Servings per Container"),
    ("ServingSz",                  "Serving Size"),
    ("Kcal",                       "Calories"),
    ("Calories from Fat from Saturated", "Calories from Saturated Fat"),
    ("Nutrient",                   None),  # We'll populate from the nutrient list
    ("Quantity",                   None),  # We'll populate from the nutrient list
    ("Percent Allowance",          "Percent Allowance"),
    ("Comments",                   "Comments"),
    ("Ingredients",                "Ingredients"),
    ("Claims",                     "Claims"),
    ("Suggested Use",              "Suggested Use"),
    ("Warnings",                   "Warnings"),
    ("Origin",                     "Origin"),
    ("Storage",                    "Storage"),
    ("Weight",                     "Weight"),
]

# Regex to match each “nutrient(…)” item safely (including decimals with commas):
# e.g. "Bílkoviny(1 g)", "Tuky(0,5 g)", "Nasycené mastné kyseliny(0,1 g)"
NUTRIENT_ITEM_REGEX = re.compile(r'([^,]+\([^)]*\))')

# Regex to split out the nutrient name vs. quantity from something like "Bílkoviny(1 g)"
NUTRIENT_NAME_AND_QTY_REGEX = re.compile(r'(.*?)\((.*?)\)')

def parse_nutrients(nutrient_str):
    """
    Returns a list of (nutrient_name, quantity) from the raw "Nutrient" field.
    Example:
      "Bílkoviny(1 g), Tuky(0,5 g), Nasycené mastné kyseliny(0,1 g)"
    => [
         ("Bílkoviny", "1 g"),
         ("Tuky", "0,5 g"),
         ("Nasycené mastné kyseliny", "0,1 g")
       ]
    """
    items = NUTRIENT_ITEM_REGEX.findall(nutrient_str or "")
    results = []
    for item in items:
        item = item.strip()
        match = NUTRIENT_NAME_AND_QTY_REGEX.match(item)
        if match:
            nutrient_name = match.group(1).strip()
            quantity = match.group(2).strip()
            results.append((nutrient_name, quantity))
        else:
            # If it doesn't match for some reason, keep the entire item as the name
            results.append((item, ""))
    return results

def build_rows_for_product(product):
    """
    Given a product dictionary (from JSON),
    return a list of row dicts—one row for each nutrient.

    For the first row, fill in all product columns plus the first nutrient.
    For subsequent nutrient rows, leave product columns blank, only fill Nutrient & Quantity.
    If there are no nutrients, return a single row with product data and empty nutrient columns.
    """
    rows = []
    # Parse out the list of (nutrient, quantity) pairs
    nutrient_pairs = parse_nutrients(product.get("Nutrient", ""))

    if not nutrient_pairs:
        # No nutrients, just one row with product data + blank Nutrient/Quantity
        row = build_row(product, nutrient_name="", quantity="", is_first_row=True)
        rows.append(row)
    else:
        # For each nutrient pair, build a row
        for i, (nut_name, nut_qty) in enumerate(nutrient_pairs):
            is_first = (i == 0)  # True only for the first nutrient row
            row = build_row(product, nut_name, nut_qty, is_first_row=is_first)
            rows.append(row)

    return rows

def build_row(product_data, nutrient_name, quantity, is_first_row):
    """
    Create a dict keyed by CSV headers from COLUMN_MAPPING.
    - If is_first_row=True, fill product columns from product_data.
    - Otherwise, leave them blank.
    - Always fill 'Nutrient' and 'Quantity' with the passed values.
    """
    row = {}
    for (csv_col, json_key) in COLUMN_MAPPING:
        if csv_col == "Nutrient":
            row[csv_col] = nutrient_name
        elif csv_col == "Quantity":
            row[csv_col] = quantity
        else:
            if is_first_row and json_key:  # fill product data only on first row
                row[csv_col] = product_data.get(json_key, "")
            else:
                # either not first row, or no JSON key to map
                row[csv_col] = ""
    return row

def convert_json_to_csv(json_path, csv_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build the list of CSV headers (the left side of each tuple)
    csv_headers = [col[0] for col in COLUMN_MAPPING]

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()

        # For each product, get the rows needed and write them
        for product in data:
            product_rows = build_rows_for_product(product)
            for row in product_rows:
                writer.writerow(row)

    print(f"Data written to {csv_path}")

if __name__ == "__main__":
    convert_json_to_csv(input_json, output_csv)