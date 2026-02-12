"""
build_import_json_study_contracts.py

Reads three CSVs using fixed filenames and generates a single import JSON file
containing an array of study objects, each with nested assets[] and study-level contracts[].

- There are ONLY study-level contracts (no asset-level contracts).
- UUIDs are NOT present in the JSON; the importer will generate them using CaseRef/AssetRef mappings.

Files:
  STUDIES_FILE   -> studies.csv
  ASSETS_FILE    -> assets.csv
  CONTRACTS_FILE -> contracts.csv     (all contracts are study-level)
  OUTPUT_FILE    -> import.json

Adjust the constants below as needed.
"""

import csv
import json
from datetime import datetime
from typing import Dict, List, Optional


STUDIES_FILE = "studies.csv"
ASSETS_FILE = "assets.csv"
CONTRACTS_FILE = "contracts.csv"
OUTPUT_FILE = "import.json"

# Pretty-print indentation (set to None for compact)
JSON_INDENT = 2

# Validate date fields strictly as YYYY-MM-DD
VALIDATE_DATES = True

def clean_headers(reader: csv.DictReader) -> None:
    """Clean CSV headers by stripping BOM, whitespace, and quotes."""
    reader.fieldnames = [
        h.lstrip("\ufeff").strip().strip('"') for h in reader.fieldnames
    ]


def to_bool(s: Optional[str]) -> bool:
    return str(s or "").strip().lower() in {"true", "1", "yes", "y"}


def parse_date(date_str: str) -> Optional[str]:
    """
    Parse a CSV date in DD/MM/YYYY format and return an ISO string YYYY-MM-DD.
    
    Returns:
        str: ISO date string (YYYY-MM-DD) if valid
        None: if input is empty or invalid
    """
    ds = (date_str or "").strip()
    if not ds:
        return None
    try:
        dt = datetime.strptime(ds, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")  # return ISO string directly
    except ValueError:
        return None
    

def validate_json_date(date_str: str) -> Optional[datetime]:
    """
    Parse a strict ISO date (YYYY-MM-DD).

    Returns:
      datetime if valid
      None if empty or invalid
    """
    ds = (date_str or "").strip()
    if not ds:
        return None

    try:
        return datetime.strptime(ds, "%Y-%m-%d")
    except ValueError:
        return None


def read_studies(filename: str) -> Dict[str, dict]:
    """
    Return dict CaseRef -> study dict (without assets/contracts yet).

    Expected headers include (missing optional columns are fine):
      CaseRef,OwnerUserID,AdminUserID,Title,ApprovalStatus,Description,DataControllerOrganisation,
      InvolvesUclSponsorship,InvolvesCag,CagReference,InvolvesEthicsApproval,InvolvesHraApproval,
      IrasId,IsNhsAssociated,InvolvesNhsEngland,NhsEnglandReference,InvolvesMnca,RequiresDspt,
      RequiresDbs,IsDataProtectionOfficeRegistered,DataProtectionNumber,InvolvesThirdParty,
      InvolvesExternalUsers,InvolvesParticipantConsent,InvolvesIndirectDataCollection,
      InvolvesDataProcessingOutsideUkEea,Feedback
    """
    studies: Dict[str, dict] = {}
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        clean_headers(reader)
        for i, row in enumerate(reader, start=2):  # header is line 1
            case_ref = (row.get("CaseRef") or "").strip()
            if not case_ref:
                raise ValueError(f"Study row missing CaseRef (line {i})")
            # if case_ref in studies:
            #     raise ValueError(f"Duplicate CaseRef in studies.csv at line {i}: {case_ref}")

            signoff_raw = row.get("IAOSignoff")
            last_signoff = parse_date(signoff_raw)

            studies[case_ref] = {
                "caseref": case_ref,
                "owner_user_id": (row.get("OwnerUserID") or "").strip(),
                "admin_user_id": (row.get("AdminUserID") or "").strip(),
                "title": (row.get("Title") or "").strip(),
                "approval_status": (row.get("ApprovalStatus") or "").strip(),
                "description": ((row.get("Description") or "").strip() or None),
                "data_controller_organisation": (row.get("DataControllerOrganisation") or "").strip(),
                "involves_ucl_sponsorship": to_bool(row.get("InvolvesUclSponsorship")),
                "involves_cag": to_bool(row.get("InvolvesCag")),
                "cag_reference": ((row.get("CagReference") or "").strip() or None),
                "involves_ethics_approval": to_bool(row.get("InvolvesEthicsApproval")),
                "involves_hra_approval": to_bool(row.get("InvolvesHraApproval")),
                "iras_id": ((row.get("IrasId") or "").strip() or None),
                "is_nhs_associated": to_bool(row.get("IsNhsAssociated")),
                "involves_nhs_england": to_bool(row.get("InvolvesNhsEngland")),
                "nhs_england_reference": ((row.get("NhsEnglandReference") or "").strip() or None),
                "involves_mnca": to_bool(row.get("InvolvesMnca")),
                "requires_dspt": to_bool(row.get("RequiresDspt")),
                "requires_dbs": to_bool(row.get("RequiresDbs")),
                "is_data_protection_office_registered": (True if ((row.get("DataProtectionNumber") or "").strip()) else None),
                "data_protection_number": ((row.get("DataProtectionNumber") or "").strip() or None),
                "involves_third_party": to_bool(row.get("InvolvesThirdParty")),
                "involves_external_users": to_bool(row.get("InvolvesExternalUsers")),
                "involves_participant_consent": to_bool(row.get("InvolvesParticipantConsent")),
                "involves_indirect_data_collection": to_bool(row.get("InvolvesIndirectDataCollection")),
                "involves_data_processing_outside_uk_eea": to_bool(row.get("InvolvesDataProcessingOutsideUkEea")),
                "dsh_active": to_bool(row.get("DSHActive")),
                "last_signoff" : last_signoff,
                "feedback": ((row.get("Feedback") or "").strip() or None),
                

                "contracts": [],
                "assets": [],
            }
    return studies


def read_assets_by_case(filename: str) -> Dict[str, List[dict]]:
    """
    Return dict CaseRef -> [asset dict].

    Expected headers include:
      CaseRef,AssetRef,Title,Description,ClassificationImpact,Tier,Protection,LegalBasis,Format,
      ExpiresAt,RequiresContract,HasDspt,StoredOutsideUkEea,Status,Locations
    """
    grouped: Dict[str, List[dict]] = {}
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        clean_headers(reader)
        for i, row in enumerate(reader, start=2):
            case_ref = (row.get("CaseRef") or "").strip()
            if not case_ref:
                raise ValueError(f"Asset row missing CaseRef (line {i})")
            
            expires_raw = row.get("Next Scheduled Review")
            expires_at = parse_date(expires_raw) # `return dt.strftime("%Y-%m-%d")` i.e. returns ISO-format string

            if VALIDATE_DATES and (expires_raw or "").strip() and expires_at is None:
                raise ValueError(
                    f"Invalid date format (expected DD/MM/YYYY) in assets.csv "
                    f"line {i}: {expires_raw!r}")

            asset = {
                "creator_userID": (row.get("Created By") or "").strip(),
                "caseref": case_ref,
                "asset_sp_id": (row.get("ID") or "").strip(),  # optional natural key for assets
                "title": (row.get("Description") or "").strip(),
                "description": (row.get("Description") or "").strip(),
                "classification_impact": (row.get("Classification") or "").strip(),
                "tier": int(row.get("Tier") or "0"),
                "protection": (row.get("Impact Mitigation") or "").strip(),
                "legal_basis": (row.get("Legal Basis") or "").strip(),
                "format": (row.get("Format") or "").strip(),
                "expires_at": expires_at,
                "requires_contract": to_bool(row.get("RequiresContract")),
                "has_dspt": to_bool(row.get("DSP Toolkit")),
                "stored_outside_uk_eea": to_bool(row.get("Outside EEA")),
                "status": (row.get("STATUS") or "").strip(),
                "locations": (row.get("Current Location")),
                # no contracts at asset level
            }
            grouped.setdefault(case_ref, []).append(asset)
    return grouped


def read_study_contracts(filename: str) -> Dict[str, List[dict]]:
    """
    Return dict CaseRef -> [study-level contracts].

    Expected headers include:
      CaseRef,ID,Filename,Status,StartDate,ExpiryDate,OrganisationSignatory,ThirdPartyName,CreatorUsername
    """
    grouped: Dict[str, List[dict]] = {}
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        clean_headers(reader)
        for i, row in enumerate(reader, start=2):
            case_ref = (row.get("CaseRef") or "").strip()
            if not case_ref:
                raise ValueError(f"Contract row missing CaseRef (line {i})")
            
            start_raw = row.get("Agreement date")
            start_date = parse_date(start_raw)

            if VALIDATE_DATES and (start_raw or "").strip() and start_date is None:
                raise ValueError(
                    f"Invalid date format (expected DD/MM/YYYY) in contracts.csv "
                    f"line {i}: {start_raw!r}")
            
            end_raw = row.get("Contract expiry or review date")
            end_date = parse_date(end_raw)

            if VALIDATE_DATES and (end_raw or "").strip() and end_date is None:
                raise ValueError(
                    f"Invalid date format (expected DD/MM/YYYY) in contracts.csv "
                    f"line {i}: {end_raw!r}")

            contract = {
                "creator_userID": (row.get("Created By") or "").strip(),
                "caseref": case_ref,
                "contract_sp_id": (row.get("ID") or "").strip(),
                "filename": (row.get("Agreement Reference") or "").strip(),
                "status": (row.get("STATUS") or "").strip(),
                "start_date": start_date,  # ISO-format string
                "expiry_date": end_date,  # ISO-format string
                "organisation_signatory": ((row.get("UCL signatory") or "").strip() or None),
                "third_party_name": ((row.get("Third party") or "").strip() or None),
                "creator_username": ((row.get("CreatorUsername") or "").strip() or None),
            }
            grouped.setdefault(case_ref, []).append(contract)
    return grouped


def build_import_json(
    studies: Dict[str, dict],
    assets_by_case: Dict[str, List[dict]],
    study_contracts_by_case: Dict[str, List[dict]],
) -> List[dict]:
    output: List[dict] = []

    for case_ref, study in studies.items():
        # Study-level contracts
        study["contracts"] = study_contracts_by_case.get(case_ref, [])

        # Assets for this study
        assets = assets_by_case.get(case_ref, [])
        for a in assets:
            expiry = a.get("expires_at")
            if expiry is not None:
                a["expires_at"] = expiry

        # Sort assets deterministically (by asset_sp_id, then title)
        assets.sort(key=lambda a: (a.get("asset_sp_id", ""), a.get("title", "")))
        study["assets"] = assets

        output.append(study)

    # Sort studies by CaseRef for deterministic output
    output.sort(key=lambda s: s.get("caseref", ""))
    return output


def validate(import_data: List[dict], validate_dates: bool = False) -> List[str]:
    errors: List[str] = []
    seen_case: set[str] = set()
    seen_asset: set[str] = set()
    seen_contract: set[str] = set()

    for s in import_data:
        cr = s.get("caseref", "")
        if not cr:
            errors.append("Study missing CaseRef")
        elif cr in seen_case:
            errors.append(f"Duplicate CaseRef in merged data: {cr}")
        else:
            seen_case.add(cr)

        # study-level contracts only
        for c in s.get("contracts", []):
            cref = c.get("contract_sp_id", "")
            if not cref:
                errors.append(f"Study {cr}: contract missing contract_sp_id")
            elif cref in seen_contract:
                errors.append(f"Duplicate contract_sp_id: {cref}")
            else:
                seen_contract.add(cref)
            if validate_dates:
                sd = c.get("start_date") or ""
                ed = c.get("expiry_date") or ""
                if sd and not validate_json_date(sd):
                    errors.append(f"Study {cr}: contract {cref} invalid start_date: {sd}")
                if ed and not validate_json_date(ed):
                    errors.append(f"Study {cr}: contract {cref} invalid expiry_date: {ed}")

        # assets (no asset-level contracts)
        for a in s.get("assets", []):
            aref = a.get("asset_sp_id", "")
            if aref:
                if aref in seen_asset:
                    errors.append(f"Duplicate asset_sp_id: {aref}")
                else:
                    seen_asset.add(aref)
            if validate_dates:
                ex = a.get("expires_at") or ""
                if ex and not validate_json_date(ex):
                    errors.append(f"Study {cr}: asset {aref} invalid expires_at: {ex}")

    return errors


def main() -> None:
    studies = read_studies(STUDIES_FILE)
    assets_by_case = read_assets_by_case(ASSETS_FILE)
    study_contracts_by_case = read_study_contracts(CONTRACTS_FILE)

    import_data = build_import_json(studies, assets_by_case, study_contracts_by_case)

    errs = validate(import_data, validate_dates=VALIDATE_DATES)
    if errs:
        print(f"Validation found {len(errs)} issue(s):")
        for e in errs:
            print(" -", e)
        # import sys; sys.exit(1)  # uncomment to fail on validation errors

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(import_data, f, ensure_ascii=False, indent=JSON_INDENT)

    print(f"Wrote {OUTPUT_FILE} with {len(import_data)} studies")

if __name__ == "__main__":
    main()
