"""Router for Data Import/Export operations."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.auth.dependencies import get_current_user_id
from app.models.data_io import ImportResult, ImportValidationResult
from app.services.export_service import ExportService
from app.services.import_service import ImportService

router = APIRouter(prefix="/data", tags=["Data Import/Export"])


# ===== IMPORT ENDPOINTS =====


@router.post("/import/validate", response_model=ImportValidationResult)
async def validate_import_file(
    file: UploadFile = File(..., description="File to validate"),
    entity_type: str = Query(..., description="Entity type: clients or leads"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Validate import file before processing."""
    service = ImportService(user_id)
    try:
        # Validate file type
        if not (
            file.filename.endswith(".xlsx")
            or file.filename.endswith(".xls")
            or file.filename.endswith(".csv")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Please upload Excel (.xlsx, .xls) or CSV (.csv) file.",
            )

        result = await service.validate_import_file(file, entity_type)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate file: {str(e)}",
        )


@router.post("/import/clients", response_model=ImportResult)
async def import_clients(
    file: UploadFile = File(..., description="Excel or CSV file with client data"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Import clients from Excel/CSV file."""
    service = ImportService(user_id)
    try:
        # Validate file type
        if not (
            file.filename.endswith(".xlsx")
            or file.filename.endswith(".xls")
            or file.filename.endswith(".csv")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Please upload Excel (.xlsx, .xls) or CSV (.csv) file.",
            )

        result = await service.import_clients_from_excel(file)
        return ImportResult(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import clients: {str(e)}",
        )


@router.post("/import/leads", response_model=ImportResult)
async def import_leads(
    file: UploadFile = File(..., description="Excel or CSV file with lead data"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Import leads from Excel/CSV file."""
    service = ImportService(user_id)
    try:
        # Validate file type
        if not (
            file.filename.endswith(".xlsx")
            or file.filename.endswith(".xls")
            or file.filename.endswith(".csv")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Please upload Excel (.xlsx, .xls) or CSV (.csv) file.",
            )

        result = await service.import_leads_from_excel(file)
        return ImportResult(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import leads: {str(e)}",
        )


@router.get("/import/template/{entity_type}")
async def get_import_template(
    entity_type: str,
    user_id: UUID = Depends(get_current_user_id),
):
    """Download Excel template for import."""
    service = ImportService(user_id)
    try:
        if entity_type not in ["clients", "leads"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid entity type. Use 'clients' or 'leads'.",
            )

        template_bytes = service.get_import_template(entity_type)
        filename = f"{entity_type}_import_template.xlsx"

        return Response(
            content=template_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}",
        )


# ===== EXPORT ENDPOINTS =====


@router.get("/export/clients")
async def export_clients(
    area: Optional[str] = Query(None, description="Filter by area"),
    risk_profile: Optional[str] = Query(None, description="Filter by risk profile"),
    occupation: Optional[str] = Query(None, description="Filter by occupation"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Export clients to Excel file."""
    service = ExportService(user_id)
    try:
        # Build filters
        filters = {}
        if area:
            filters["area"] = area
        if risk_profile:
            filters["risk_profile"] = risk_profile
        if occupation:
            filters["occupation"] = occupation

        excel_bytes = await service.export_clients_to_excel(
            filters if filters else None
        )

        filename = f"clients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export clients: {str(e)}",
        )


@router.get("/export/leads")
async def export_leads(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Export leads to Excel file."""
    service = ExportService(user_id)
    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if source:
            filters["source"] = source

        excel_bytes = await service.export_leads_to_excel(filters if filters else None)

        filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export leads: {str(e)}",
        )


@router.get("/export/tasks")
async def export_tasks(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Export tasks to Excel file."""
    service = ExportService(user_id)
    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if priority:
            filters["priority"] = priority

        excel_bytes = await service.export_tasks_to_excel(filters if filters else None)

        filename = f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export tasks: {str(e)}",
        )


@router.get("/export/touchpoints")
async def export_touchpoints(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    interaction_type: Optional[str] = Query(
        None, description="Filter by interaction type"
    ),
    user_id: UUID = Depends(get_current_user_id),
):
    """Export touchpoints to Excel file."""
    service = ExportService(user_id)
    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if interaction_type:
            filters["interaction_type"] = interaction_type

        excel_bytes = await service.export_touchpoints_to_excel(
            filters if filters else None
        )

        filename = f"touchpoints_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export touchpoints: {str(e)}",
        )


@router.get("/export/goals")
async def export_goals(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    goal_type: Optional[str] = Query(None, description="Filter by goal type"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Export goals to Excel file."""
    service = ExportService(user_id)
    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if goal_type:
            filters["goal_type"] = goal_type

        excel_bytes = await service.export_goals_to_excel(filters if filters else None)

        filename = f"goals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export goals: {str(e)}",
        )


@router.get("/export/opportunities")
async def export_opportunities(
    opportunity_stage: Optional[str] = Query(
        None, description="Filter by opportunity stage"
    ),
    opportunity_type: Optional[str] = Query(
        None, description="Filter by opportunity type"
    ),
    user_id: UUID = Depends(get_current_user_id),
):
    """Export business opportunities to Excel file."""
    service = ExportService(user_id)
    try:
        # Build filters
        filters = {}
        if opportunity_stage:
            filters["opportunity_stage"] = opportunity_stage
        if opportunity_type:
            filters["opportunity_type"] = opportunity_type

        excel_bytes = await service.export_opportunities_to_excel(
            filters if filters else None
        )

        filename = (
            f"opportunities_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export opportunities: {str(e)}",
        )


@router.get("/export/all")
async def export_all_data(
    user_id: UUID = Depends(get_current_user_id),
):
    """Export all data to a multi-sheet Excel workbook."""
    service = ExportService(user_id)
    try:
        excel_bytes = await service.export_all_data()

        filename = f"mfd_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export all data: {str(e)}",
        )
