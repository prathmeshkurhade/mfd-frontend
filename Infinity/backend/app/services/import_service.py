"""Data Import Service for Excel/CSV import."""

import re
from datetime import date, datetime
from io import BytesIO
from typing import Any, Dict, List
from uuid import UUID

import pandas as pd
from fastapi import UploadFile
from openpyxl import Workbook

from app.database import supabase


class ImportService:
    """Service for importing data from Excel/CSV files."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def import_clients_from_excel(self, file: UploadFile) -> Dict[str, Any]:
        """Import clients from Excel/CSV file."""
        try:
            # Read file
            contents = await file.read()
            
            # Determine file type and read with pandas
            if file.filename.endswith(".csv"):
                df = pd.read_csv(BytesIO(contents))
            else:
                df = pd.read_excel(BytesIO(contents))

            # Validate required columns
            required_columns = ["name", "phone"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

            # Track results
            total_rows = len(df)
            imported = 0
            skipped = 0
            failed = 0
            errors = []

            # Process each row
            for index, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row["name"]) or pd.isna(row["phone"]):
                        skipped += 1
                        errors.append(
                            {"row": index + 2, "error": "Missing name or phone"}
                        )
                        continue

                    # Parse phone
                    phone = self.parse_phone(str(row["phone"]))

                    # Check duplicate
                    existing = (
                        supabase.table("clients")
                        .select("id")
                        .eq("user_id", str(self.user_id))
                        .eq("phone", phone)
                        .eq("is_deleted", False)
                        .execute()
                    )

                    if existing.data:
                        skipped += 1
                        errors.append(
                            {
                                "row": index + 2,
                                "error": f"Duplicate phone: {phone}",
                            }
                        )
                        continue

                    # Prepare client data
                    client_data = {
                        "user_id": str(self.user_id),
                        "name": str(row["name"]).strip(),
                        "phone": phone,
                    }

                    # Optional fields
                    if "email" in df.columns and not pd.isna(row["email"]):
                        client_data["email"] = str(row["email"]).strip()

                    if "birthdate" in df.columns and not pd.isna(row["birthdate"]):
                        parsed_date = self.parse_date(row["birthdate"])
                        if parsed_date:
                            client_data["birthdate"] = parsed_date.isoformat()

                    if "gender" in df.columns and not pd.isna(row["gender"]):
                        client_data["gender"] = str(row["gender"]).lower()

                    if "occupation" in df.columns and not pd.isna(row["occupation"]):
                        client_data["occupation"] = str(row["occupation"]).lower().replace(" ", "_")

                    if "area" in df.columns and not pd.isna(row["area"]):
                        client_data["area"] = str(row["area"]).strip()

                    if "aum" in df.columns and not pd.isna(row["aum"]):
                        try:
                            client_data["aum"] = float(row["aum"])
                        except ValueError:
                            pass

                    if "sip_amount" in df.columns and not pd.isna(row["sip_amount"]):
                        try:
                            client_data["sip_amount"] = float(row["sip_amount"])
                        except ValueError:
                            pass

                    # Insert client
                    supabase.table("clients").insert(client_data).execute()
                    imported += 1

                except Exception as e:
                    failed += 1
                    errors.append({"row": index + 2, "error": str(e)})

            return {
                "total_rows": total_rows,
                "imported": imported,
                "skipped": skipped,
                "failed": failed,
                "errors": errors[:10],  # Limit to first 10 errors
            }

        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

    async def import_leads_from_excel(self, file: UploadFile) -> Dict[str, Any]:
        """Import leads from Excel/CSV file."""
        try:
            # Read file
            contents = await file.read()

            if file.filename.endswith(".csv"):
                df = pd.read_csv(BytesIO(contents))
            else:
                df = pd.read_excel(BytesIO(contents))

            # Validate required columns
            required_columns = ["name", "phone"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

            # Track results
            total_rows = len(df)
            imported = 0
            skipped = 0
            failed = 0
            errors = []

            # Process each row
            for index, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row["name"]) or pd.isna(row["phone"]):
                        skipped += 1
                        errors.append(
                            {"row": index + 2, "error": "Missing name or phone"}
                        )
                        continue

                    # Parse phone
                    phone = self.parse_phone(str(row["phone"]))

                    # Check duplicate
                    existing = (
                        supabase.table("leads")
                        .select("id")
                        .eq("user_id", str(self.user_id))
                        .eq("phone", phone)
                        .execute()
                    )

                    if existing.data:
                        skipped += 1
                        errors.append(
                            {"row": index + 2, "error": f"Duplicate phone: {phone}"}
                        )
                        continue

                    # Prepare lead data
                    lead_data = {
                        "user_id": str(self.user_id),
                        "name": str(row["name"]).strip(),
                        "phone": phone,
                        "status": "follow_up",
                    }

                    # Optional fields
                    if "email" in df.columns and not pd.isna(row["email"]):
                        lead_data["email"] = str(row["email"]).strip()

                    if "source" in df.columns and not pd.isna(row["source"]):
                        lead_data["source"] = str(row["source"]).lower().replace(" ", "_")

                    if "status" in df.columns and not pd.isna(row["status"]):
                        lead_data["status"] = str(row["status"]).lower().replace(" ", "_")

                    if "area" in df.columns and not pd.isna(row["area"]):
                        lead_data["area"] = str(row["area"]).strip()

                    # Insert lead
                    supabase.table("leads").insert(lead_data).execute()
                    imported += 1

                except Exception as e:
                    failed += 1
                    errors.append({"row": index + 2, "error": str(e)})

            return {
                "total_rows": total_rows,
                "imported": imported,
                "skipped": skipped,
                "failed": failed,
                "errors": errors[:10],
            }

        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

    async def validate_import_file(
        self, file: UploadFile, entity_type: str
    ) -> Dict[str, Any]:
        """Validate import file before processing."""
        try:
            # Read file
            contents = await file.read()

            if file.filename.endswith(".csv"):
                df = pd.read_csv(BytesIO(contents))
            else:
                df = pd.read_excel(BytesIO(contents))

            # Define required columns by entity type
            required_columns_map = {
                "clients": ["name", "phone"],
                "leads": ["name", "phone"],
            }

            required_columns = required_columns_map.get(entity_type, [])

            # Check which columns are present
            columns_found = list(df.columns)
            columns_missing = [
                col for col in required_columns if col not in columns_found
            ]

            return {
                "valid": len(columns_missing) == 0,
                "columns_found": columns_found,
                "columns_missing": columns_missing,
                "row_count": len(df),
            }

        except Exception as e:
            raise ValueError(f"Failed to validate file: {str(e)}")

    def get_import_template(self, entity_type: str) -> bytes:
        """Generate Excel template for import."""
        wb = Workbook()
        ws = wb.active

        # Define headers by entity type
        if entity_type == "clients":
            headers = [
                "name",
                "phone",
                "email",
                "birthdate",
                "gender",
                "marital_status",
                "occupation",
                "income_group",
                "area",
                "risk_profile",
                "source",
                "aum",
                "sip_amount",
                "notes",
            ]
            ws.title = "Clients Import"

        elif entity_type == "leads":
            headers = [
                "name",
                "phone",
                "email",
                "gender",
                "marital_status",
                "occupation",
                "income_group",
                "area",
                "source",
                "status",
                "scheduled_date",
                "notes",
            ]
            ws.title = "Leads Import"

        else:
            headers = ["name", "phone", "email"]
            ws.title = "Import Template"

        # Add headers
        ws.append(headers)

        # Add example row
        if entity_type == "clients":
            example = [
                "John Doe",
                "+919876543210",
                "john@example.com",
                "1990-01-15",
                "male",
                "married",
                "service",
                "l12_1_to_24",
                "Mumbai",
                "moderate",
                "referral",
                "1000000",
                "5000",
                "Sample notes",
            ]
        elif entity_type == "leads":
            example = [
                "Jane Smith",
                "+919876543211",
                "jane@example.com",
                "female",
                "single",
                "business",
                "l24_1_to_48",
                "Delhi",
                "social_media",
                "follow_up",
                "2026-02-01",
                "Sample notes",
            ]
        else:
            example = ["Sample Name", "+919876543210", "sample@example.com"]

        ws.append(example)

        # Save to BytesIO
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def parse_phone(self, phone: str) -> str:
        """Normalize phone to +91XXXXXXXXXX format."""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)

        # Handle different formats
        if digits.startswith("91") and len(digits) == 12:
            return f"+{digits}"
        elif len(digits) == 10:
            return f"+91{digits}"
        elif digits.startswith("0") and len(digits) == 11:
            return f"+91{digits[1:]}"
        else:
            # Return as is with +91 prefix if not already there
            if phone.startswith("+91"):
                return phone
            return f"+91{digits[-10:]}" if len(digits) >= 10 else phone

    def parse_date(self, date_value: Any) -> date:
        """Parse date from various formats."""
        if pd.isna(date_value):
            return None

        try:
            # If it's already a datetime
            if isinstance(date_value, datetime):
                return date_value.date()

            # If it's a date
            if isinstance(date_value, date):
                return date_value

            # If it's a string
            if isinstance(date_value, str):
                # Try DD/MM/YYYY
                try:
                    return datetime.strptime(date_value, "%d/%m/%Y").date()
                except ValueError:
                    pass

                # Try YYYY-MM-DD
                try:
                    return datetime.strptime(date_value, "%Y-%m-%d").date()
                except ValueError:
                    pass

                # Try DD-MM-YYYY
                try:
                    return datetime.strptime(date_value, "%d-%m-%Y").date()
                except ValueError:
                    pass

            # If it's a pandas Timestamp
            if hasattr(date_value, "date"):
                return date_value.date()

            return None

        except Exception:
            return None
