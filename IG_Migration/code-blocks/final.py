import csv
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Record:
    username: str
    has_signed_agreement: bool
    nhsd_training_completed_at: datetime | None


TRAINING_FILE = "training.csv"
AGREEMENT_FILE = "agreement.csv"
OUTPUT_FILE = "import.csv"

def normalise_username(value: str) -> str:
    """
    Normalises usernames to required email format so that training and agreement records align.

    Rules:
    - Trim whitespace
    - Lowercase
    - If it contains '@', treat it as an email address and convert to EXT UPN:
        - Replace '@' with '_'
        - Append '#EXT#@liveuclac.onmicrosoft.com'
    - If it does NOT contain '@', append '@ucl.ac.uk'
    """
    value = value.strip().lower()

    if "@" in value:
        value = value.replace("@", "_")
        return f"{value}#EXT#@liveuclac.onmicrosoft.com"
    # Need to deal with nop- prefexied UserIDs from the Training list 
    return f"{value}@ucl.ac.uk"


def clean_headers(reader: csv.DictReader) -> None:
    """Clean CSV headers by stripping BOM, whitespace, and quotes."""
    reader.fieldnames = [
        h.lstrip("\ufeff").strip().strip('"') for h in reader.fieldnames
    ]


def load_training() -> dict[str, datetime | None]:
    training = {}

    with open(TRAINING_FILE, newline="") as f:
        reader = csv.DictReader(f)
        clean_headers(reader)

        for row in reader:

            other_email = (row.get("Other email") or "").strip()
            userid = (row.get("UserID") or "").strip()

            if other_email:
                user = normalise_username(other_email)
            elif userid:
                user = normalise_username(userid)
            else:
                continue  # if no userid or ext email, skip

            date_str = (row.get("LastTrained") or "").strip()
            training_date = None
            if date_str:
                try:
                    training_date = datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    pass

            training[user] = training_date

    return training


def load_agreements() -> dict[str, bool]:
    agreements = {}
    with open(AGREEMENT_FILE, newline="") as f:
        reader = csv.DictReader(f)
        clean_headers(reader)

        for row in reader:
            # Skip rows missing required columns
            if not row.get("UserID") or not row.get("Approved"):
                continue

            user = normalise_username(row.get("UserID"))
            has_signed = row.get("Approved").strip().lower() == "true"

            agreements[user] = has_signed

    return agreements


def merge_records() -> list[Record]:
    training = load_training()
    agreements = load_agreements()

    # All users who appear in either CSV, sorted alphabetically
    all_users = sorted(set(training) | set(agreements))

    merged_records: list[Record] = []

    for user in all_users:
        has_agreed = agreements.get(user, False)
        training_date = training.get(user, None)

        merged_records.append(
            Record(
                username=user,
                has_signed_agreement=has_agreed,
                nhsd_training_completed_at=training_date,
            )
        )
    return merged_records


def write_output(records: list[Record]):
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        
        for r in records:
            writer.writerow([
                r.username,
                str(r.has_signed_agreement).lower(),  # "True" or "False" to "true" or "false"
                r.nhsd_training_completed_at.strftime("%Y-%m-%d") if r.nhsd_training_completed_at else "",
            ])


def main():
    records = merge_records()
    write_output(records)


if __name__ == "__main__":
    main()
