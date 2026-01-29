from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import (
    FindingRead,
    JobRead,
    RulepackCreate,
    RulepackRead,
    RulepackSelectionUpdate,
)
from common.config import settings
from common.db import SessionLocal, init_db
from common.logging import configure_logging
from common.utils import ensure_within_base, safe_filename
from findings.repository import FindingsRepository
from jobs.repository import JobRepository
from purview.exporter import ExportValidationError, build_rule_package
from purview.repository import RulepackRepository
from sit.repository import SitRepository
from sit.schemas import (
    KeywordListCreate,
    KeywordListRead,
    SitCreate,
    SitDetailRead,
    SitExportRequest,
    SitRead,
    SitVersionCreate,
    SitVersionRead,
)
from workers.tasks import scan_file_job

configure_logging()
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup() -> None:
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    init_db()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.get("/ui/scans", response_class=HTMLResponse)
def scans_page(request: Request):
    return templates.TemplateResponse("scans.html", {"request": request})


@app.get("/ui/findings", response_class=HTMLResponse)
def findings_page(request: Request):
    return templates.TemplateResponse("findings.html", {"request": request})


@app.get("/ui/sits", response_class=HTMLResponse)
def sits_page(request: Request):
    return templates.TemplateResponse("sits.html", {"request": request})


@app.get("/ui/rulepacks", response_class=HTMLResponse)
def rulepacks_page(request: Request):
    return templates.TemplateResponse("rulepacks.html", {"request": request})


@app.post("/scan")
async def scan_file(
    file: Optional[UploadFile] = File(default=None),
    path: Optional[str] = Form(default=None),
    session=Depends(get_session),
):
    if not file and not path:
        raise HTTPException(status_code=400, detail="File upload or path is required")

    job_id = str(uuid.uuid4())
    repo = JobRepository(session)

    if file:
        safe_name = safe_filename(file.filename or "upload")
        job_dir = settings.storage_path / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        destination = job_dir / safe_name
        with destination.open("wb") as handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        repo.create(job_id, file_name=safe_name)
        scan_file_job.delay(job_id, str(destination))
        return {"job_id": job_id}

    resolved_path = ensure_within_base(Path(path), settings.scan_root)
    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    repo.create(job_id, file_name=resolved_path.name)
    scan_file_job.delay(job_id, str(resolved_path))
    return {"job_id": job_id}


@app.get("/jobs/{job_id}", response_model=JobRead)
def job_status(job_id: str, session=Depends(get_session)):
    repo = JobRepository(session)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs", response_model=list[JobRead])
def list_jobs(session=Depends(get_session)):
    repo = JobRepository(session)
    return repo.list_jobs()


@app.get("/findings", response_model=list[FindingRead])
def list_findings(
    job_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    session=Depends(get_session),
):
    repo = FindingsRepository(session)
    findings = repo.list_findings(job_id=job_id, entity_type=entity_type)
    return findings


@app.get("/sits", response_model=list[SitRead])
def list_sits(
    name: Optional[str] = None,
    session=Depends(get_session),
):
    repo = SitRepository(session)
    sits = repo.list_sits(name=name)
    return sits


@app.get("/sits/{sit_id}", response_model=SitDetailRead)
def get_sit(sit_id: str, session=Depends(get_session)):
    repo = SitRepository(session)
    sit = repo.get_sit(sit_id)
    if not sit:
        raise HTTPException(status_code=404, detail="SIT not found")
    return sit


@app.post("/sits", response_model=SitDetailRead)
def create_sit(sit: SitCreate, session=Depends(get_session)):
    repo = SitRepository(session)
    sit_record = repo.create_sit(sit.name, sit.description)
    _validate_supporting_logic(sit.version)
    repo.create_version(
        sit_record.id,
        entity_type=sit.version.entity_type,
        confidence=sit.version.confidence,
        source=sit.version.source,
        primary_element=sit.version.primary_element.model_dump(),
        supporting_logic=sit.version.supporting_logic.model_dump(),
        supporting_groups=[group.model_dump() for group in sit.version.supporting_groups],
    )
    return repo.get_sit(sit_record.id)


@app.post("/sits/{sit_id}/versions", response_model=SitVersionRead)
def create_sit_version(
    sit_id: str, payload: SitVersionCreate, session=Depends(get_session)
):
    repo = SitRepository(session)
    if not repo.get_sit(sit_id):
        raise HTTPException(status_code=404, detail="SIT not found")
    _validate_supporting_logic(payload)
    version = repo.create_version(
        sit_id,
        entity_type=payload.entity_type,
        confidence=payload.confidence,
        source=payload.source,
        primary_element=payload.primary_element.model_dump(),
        supporting_logic=payload.supporting_logic.model_dump(),
        supporting_groups=[group.model_dump() for group in payload.supporting_groups],
    )
    return version


@app.post("/keyword-lists", response_model=KeywordListRead)
def create_keyword_list(payload: KeywordListCreate, session=Depends(get_session)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Keyword list items required")
    repo = SitRepository(session)
    return repo.create_keyword_list(payload.name, payload.description, payload.items)


@app.get("/keyword-lists", response_model=list[KeywordListRead])
def list_keyword_lists(session=Depends(get_session)):
    repo = SitRepository(session)
    return repo.list_keyword_lists()


@app.post("/rulepacks", response_model=RulepackRead)
def create_rulepack(payload: RulepackCreate, session=Depends(get_session)):
    repo = RulepackRepository(session)
    rulepack = repo.create_rulepack(
        payload.name,
        payload.version,
        payload.description,
        payload.publisher,
        payload.locale,
    )
    return _rulepack_read(rulepack)


@app.get("/rulepacks", response_model=list[RulepackRead])
def list_rulepacks(session=Depends(get_session)):
    repo = RulepackRepository(session)
    return [_rulepack_read(item) for item in repo.list_rulepacks()]


@app.get("/rulepacks/{rulepack_id}", response_model=RulepackRead)
def get_rulepack(rulepack_id: str, session=Depends(get_session)):
    repo = RulepackRepository(session)
    rulepack = repo.get_rulepack(rulepack_id)
    if not rulepack:
        raise HTTPException(status_code=404, detail="Rulepack not found")
    return _rulepack_read(rulepack)


@app.post("/rulepacks/{rulepack_id}/selections")
def update_rulepack_selections(
    rulepack_id: str,
    payload: RulepackSelectionUpdate,
    session=Depends(get_session),
):
    repo = RulepackRepository(session)
    if not repo.get_rulepack(rulepack_id):
        raise HTTPException(status_code=404, detail="Rulepack not found")
    repo.set_selections(rulepack_id, payload.version_ids)
    return {"status": "ok"}


@app.post("/rulepacks/{rulepack_id}/export")
def export_rulepack(rulepack_id: str, session=Depends(get_session)):
    rulepack_repo = RulepackRepository(session)
    sit_repo = SitRepository(session)
    rulepack = rulepack_repo.get_rulepack(rulepack_id)
    if not rulepack:
        raise HTTPException(status_code=404, detail="Rulepack not found")

    version_ids = [selection.sit_version_id for selection in rulepack.selections]
    versions = sit_repo.get_versions_by_ids(version_ids)
    try:
        xml_data = build_rule_package(rulepack, versions)
    except ExportValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=xml_data, media_type="application/xml")


@app.post("/sits/export")
def export_sits(payload: SitExportRequest, session=Depends(get_session)):
    """Deprecated: use rulepack export instead."""
    sit_repo = SitRepository(session)
    rulepack_repo = RulepackRepository(session)
    rulepack = rulepack_repo.create_rulepack(
        name="Ad hoc rulepack",
        version=datetime.utcnow().isoformat(),
        description="Deprecated export",
        publisher=None,
        locale=None,
    )
    versions = sit_repo.get_versions_by_ids(payload.version_ids)
    try:
        xml_data = build_rule_package(rulepack, versions)
    except ExportValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=xml_data, media_type="application/xml")


def _validate_supporting_logic(payload: SitVersionCreate) -> None:
    mode = payload.supporting_logic.mode
    if mode not in {"ANY", "ALL", "MIN_N"}:
        raise HTTPException(status_code=400, detail="Invalid supporting logic mode")
    if mode == "MIN_N" and (payload.supporting_logic.min_n or 0) < 1:
        raise HTTPException(status_code=400, detail="MIN_N requires min_n >= 1")
    if mode in {"ANY", "ALL", "MIN_N"} and not payload.supporting_groups:
        raise HTTPException(
            status_code=400, detail="Supporting groups required for selected mode"
        )


def _rulepack_read(rulepack) -> RulepackRead:
    return RulepackRead(
        id=rulepack.id,
        name=rulepack.name,
        version=rulepack.version,
        description=rulepack.description,
        publisher=rulepack.publisher,
        locale=rulepack.locale,
        created_at=rulepack.created_at,
        selections=[selection.sit_version_id for selection in rulepack.selections],
    )
