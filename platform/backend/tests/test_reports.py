from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.models.core import Asset
from app.services.reports import generate_report


def test_generate_html_report(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset = Asset(ip="192.0.2.1", protocols=["modbus"], tags=["lab"])
        session.add(asset)
        session.commit()
        session.refresh(asset)

        report = generate_report(
            session=session,
            scope={},
            parameters={"range": "lab"},
            fmt="html",
            title="Test Report",
            output_dir=tmp_path,
        )
        assert report.id is not None
        assert report.format == "html"
        assert Path(report.file_path).exists()
        assert Path(report.file_path).suffix == ".html"


def test_generate_pdf_and_docx(tmp_path):
    db_path = tmp_path / "test2.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset = Asset(ip="198.51.100.1", protocols=["opcua"], device_type="gateway")
        session.add(asset)
        session.commit()
        session.refresh(asset)

        pdf_report = generate_report(
            session=session,
            scope={"assets": [asset.id]},
            parameters={"scope": "single"},
            fmt="pdf",
            title="PDF Report",
            output_dir=tmp_path,
        )
        docx_report = generate_report(
            session=session,
            scope={"assets": [asset.id]},
            parameters={"scope": "single"},
            fmt="docx",
            title="DOCX Report",
            output_dir=tmp_path,
        )

        assert Path(pdf_report.file_path).exists()
        assert Path(pdf_report.file_path).suffix == ".pdf"
        assert Path(docx_report.file_path).exists()
        assert Path(docx_report.file_path).suffix == ".docx"
