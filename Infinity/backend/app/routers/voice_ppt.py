"""
Voice PPT Router
=================
Authenticated endpoints for generating voiced presentations.

Uses logged-in MFD's profile from mfd_profiles table.
Pre-built PPTs fetched from Supabase Storage. ~0.5s per request.

Endpoints:
  POST /voice-ppt/generate       → Single PPT
  POST /voice-ppt/generate-both  → ZIP with both languages
  GET  /voice-ppt/voices         → Available voice options
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
import os
import uuid
import shutil
import logging
import zipfile

from app.auth.dependencies import get_current_user
from app.services.voice_ppt_service import (
    fetch_voiced_template,
    stamp_distributor,
    get_mfd_profile,
    get_available_voices,
)
from app.models.voice_ppt import (
    GeneratePPTRequest,
    GenerateBothRequest,
)

router = APIRouter(prefix="/voice-ppt", tags=["Voice PPT"])
logger = logging.getLogger(__name__)


@router.post("/generate")
async def generate_voiced_ppt(
    request: GeneratePPTRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a personalized voiced PPT for the authenticated MFD.

    Pulls name from mfd_profiles. Audio is pre-baked.
    User only picks voice + language.
    """
    job_id = str(uuid.uuid4())[:8]
    work_dir = tempfile.mkdtemp(prefix=f"vppt_{job_id}_")

    try:
        user_id = current_user["id"]
        voice = request.voice.value
        language = request.language.value

        # Get MFD profile
        logger.info(f"[{job_id}] Fetching profile for user {user_id}")
        profile = get_mfd_profile(user_id)
        distributor_name = profile["name"]

        # Fetch pre-built voiced PPT
        lang_label = "english" if language == "en" else "hinglish"
        safe_name = distributor_name.replace(" ", "_").lower()
        filename = f"mutual_funds_{safe_name}_{lang_label}.pptx"
        ppt_path = os.path.join(work_dir, f"base_{voice}_{language}.pptx")

        logger.info(f"[{job_id}] Fetching template: {voice}/{language}")
        await fetch_voiced_template(voice, language, ppt_path)

        # Stamp distributor identity
        output_path = os.path.join(work_dir, filename)
        logger.info(f"[{job_id}] Stamping: {distributor_name}")
        stamp_distributor(
            ppt_path=ppt_path,
            distributor_name=distributor_name,
            distributor_role="MF Distributor",
            photo_path=None,
            output_path=output_path,
        )

        logger.info(f"[{job_id}] Done → {filename}")
        background_tasks.add_task(_cleanup, work_dir)

        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{job_id}] Failed: {e}", exc_info=True)
        background_tasks.add_task(_cleanup, work_dir)
        raise HTTPException(status_code=500, detail=f"PPT generation failed: {str(e)}")


@router.post("/generate-both")
async def generate_both_languages(
    request: GenerateBothRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Generate BOTH English + Hinglish voiced PPTs. Returns ZIP."""
    job_id = str(uuid.uuid4())[:8]
    work_dir = tempfile.mkdtemp(prefix=f"vppt_both_{job_id}_")

    try:
        user_id = current_user["id"]
        voice = request.voice.value

        profile = get_mfd_profile(user_id)
        distributor_name = profile["name"]
        safe_name = distributor_name.replace(" ", "_").lower()

        ppt_files = []

        for lang in ["en", "hi"]:
            lang_label = "english" if lang == "en" else "hinglish"
            filename = f"mutual_funds_{safe_name}_{lang_label}.pptx"
            ppt_path = os.path.join(work_dir, f"base_{voice}_{lang}.pptx")
            output_path = os.path.join(work_dir, filename)

            logger.info(f"[{job_id}] {lang_label}: fetch + stamp")
            await fetch_voiced_template(voice, lang, ppt_path)
            stamp_distributor(
                ppt_path=ppt_path,
                distributor_name=distributor_name,
                distributor_role="MF Distributor",
                output_path=output_path,
            )
            ppt_files.append((filename, output_path))

        zip_filename = f"voiced_ppts_{safe_name}.zip"
        zip_path = os.path.join(work_dir, zip_filename)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, fpath in ppt_files:
                zf.write(fpath, fname)

        logger.info(f"[{job_id}] Done → {zip_filename}")
        background_tasks.add_task(_cleanup, work_dir)

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{job_id}] Failed: {e}", exc_info=True)
        background_tasks.add_task(_cleanup, work_dir)
        raise HTTPException(status_code=500, detail=f"PPT generation failed: {str(e)}")


@router.get("/voices")
async def list_voices(current_user: dict = Depends(get_current_user)):
    """List available voice + language options."""
    return get_available_voices()


async def _cleanup(work_dir: str):
    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception:
        pass