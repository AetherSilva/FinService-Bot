import csv
import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from io import StringIO
from config_schema import ServiceType, config_manager
from templates import OfferData

@dataclass
class ValidationError:
    row: int
    field: str
    message: str

    def __str__(self):
        return f"Row {self.row}, Field '{self.field}': {self.message}"

@dataclass
class ValidationResult:
    valid: bool
    offers: List[OfferData]
    errors: List[ValidationError]
    warnings: List[str]

    def __str__(self):
        return f"Valid: {self.valid}, Offers: {len(self.offers)}, Errors: {len(self.errors)}"

class CSVValidator:

    REQUIRED_COLUMNS = [
        "service_type",
        "provider",
        "title_en",
        "referral_link"
    ]

    OPTIONAL_COLUMNS = [
        "title_hi",
        "title_gu",
        "description_en",
        "description_hi",
        "description_gu",
        "validity",
        "terms"
    ]

    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
        self.seen_fingerprints: set = set()

    def _normalize_url(self, url: str) -> str:
        return url.split("?")[0].split("#")[0].lower().strip()

    def _make_fingerprint(self, service_type: str, provider: str, url: str) -> str:
        normalized = self._normalize_url(url)
        raw = f"{service_type.lower()}|{provider.lower()}|{normalized}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _validate_url(self, url: str) -> bool:
        if not url:
            return False

        if not url.startswith("https://") and not url.startswith("http://"):
            return False

        return bool(self.URL_PATTERN.match(url))

    def _validate_service_type(self, service_type: str) -> Tuple[bool, Optional[str]]:
        try:
            config_manager.validate_service_type(service_type)
            return True, None
        except ValueError as e:
            return False, str(e)

    def _validate_row(self, row: Dict[str, str], row_num: int) -> Optional[OfferData]:
        row_errors = []

        for field in self.REQUIRED_COLUMNS:
            if field not in row or not row[field].strip():
                row_errors.append(
                    ValidationError(row_num, field, "Required field missing or empty")
                )

        if row_errors:
            self.errors.extend(row_errors)
            return None

        service_type = row["service_type"].strip()
        valid, error_msg = self._validate_service_type(service_type)
        if not valid:
            self.errors.append(
                ValidationError(row_num, "service_type", error_msg)
            )
            return None

        referral_link = row["referral_link"].strip()
        if not self._validate_url(referral_link):
            self.errors.append(
                ValidationError(row_num, "referral_link", "Invalid URL format")
            )
            return None

        provider = row["provider"].strip()
        fingerprint = self._make_fingerprint(service_type, provider, referral_link)

        if fingerprint in self.seen_fingerprints:
            self.warnings.append(
                f"Row {row_num}: Duplicate offer detected (same provider + URL)"
            )
            return None

        self.seen_fingerprints.add(fingerprint)

        for field in ["title_en", "title_hi", "title_gu"]:
            if field in row and row[field] and len(row[field]) > 200:
                self.warnings.append(
                    f"Row {row_num}: {field} exceeds 200 characters, will be truncated"
                )

        service_config = config_manager.get_service_config(ServiceType(service_type))

        offer = OfferData(
            service_type=service_type,
            provider=provider,
            title_en=row["title_en"].strip()[:200],
            title_hi=row.get("title_hi", "").strip()[:200] or None,
            title_gu=row.get("title_gu", "").strip()[:200] or None,
            description_en=row.get("description_en", "").strip()[:500] or None,
            description_hi=row.get("description_hi", "").strip()[:500] or None,
            description_gu=row.get("description_gu", "").strip()[:500] or None,
            referral_link=referral_link,
            validity=row.get("validity", "").strip() or None,
            terms=row.get("terms", "").strip()[:300] or None,
            icon=service_config.icon
        )

        return offer

    def validate_csv_file(self, file_path: str) -> ValidationResult:
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.validate_csv_content(f.read())

    def validate_csv_content(self, content: str) -> ValidationResult:
        self.errors = []
        self.warnings = []
        self.seen_fingerprints = set()
        offers = []

        try:
            reader = csv.DictReader(StringIO(content))

            if not reader.fieldnames:
                self.errors.append(
                    ValidationError(0, "headers", "No headers found in CSV")
                )
                return ValidationResult(False, [], self.errors, self.warnings)

            missing_required = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing_required:
                self.errors.append(
                    ValidationError(
                        0, 
                        "headers", 
                        f"Missing required columns: {', '.join(missing_required)}"
                    )
                )
                return ValidationResult(False, [], self.errors, self.warnings)

            for idx, row in enumerate(reader, start=2):  # Start at 2 (row 1 = headers)
                offer = self._validate_row(row, idx)
                if offer:
                    offers.append(offer)

            if not offers and not self.errors:
                self.warnings.append("No valid offers found in CSV")

            valid = len(self.errors) == 0 and len(offers) > 0

            return ValidationResult(
                valid=valid,
                offers=offers,
                errors=self.errors,
                warnings=self.warnings
            )

        except csv.Error as e:
            self.errors.append(
                ValidationError(0, "csv", f"CSV parsing error: {str(e)}")
            )
            return ValidationResult(False, [], self.errors, self.warnings)
        except Exception as e:
            self.errors.append(
                ValidationError(0, "system", f"Unexpected error: {str(e)}")
            )
            return ValidationResult(False, [], self.errors, self.warnings)

    def generate_template_csv(self) -> str:
        template = [
            self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS,
            [
                "credit_card",
                "HDFC Bank",
                "5% cashback on all transactions",
                "सभी लेनदेन पर 5% कैशबैक",
                "બધા વ્યવહારો પર 5% કેશબેક",
                "Unlimited cashback with no caps",
                "असीमित कैशबैक, कोई सीमा नहीं",
                "અમર્યાદિત કેશબેક, કોઈ મર્યાદા નથી",
                "https://hdfc.com/ref/abc123",
                "31 Dec 2026",
                "Subject to bank terms"
            ],
            [
                "loan_personal",
                "Bajaj Finserv",
                "Personal loan at 10.5% APR",
                "10.5% वार्षिक ब्याज दर पर व्यक्तिगत ऋण",
                "",  # No Gujarati translation
                "Quick approval, flexible tenure",
                "",
                "",
                "https://bajajfinserv.com/personal-loan?ref=xyz789",
                "15 Jan 2027",
                "Min CIBIL 700 required"
            ]
        ]

        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(template)
        return output.getvalue()


def test_validator():
    validator = CSVValidator()

    template_csv = validator.generate_template_csv()
    print("=== TEMPLATE CSV ===")
    print(template_csv)
    print("\n" + "="*60 + "\n")

    result = validator.validate_csv_content(template_csv)
    print("=== VALIDATION RESULT ===")
    print(result)
    print(f"\nValid Offers: {len(result.offers)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")

    if result.errors:
        print("\n=== ERRORS ===")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("\n=== WARNINGS ===")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.offers:
        print("\n=== SAMPLE OFFER ===")
        print(result.offers[0])


if __name__ == "__main__":
    pass
