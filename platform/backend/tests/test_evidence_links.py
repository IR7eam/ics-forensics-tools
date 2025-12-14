from sqlmodel import Session, SQLModel, create_engine, select

from app.models.core import EvidenceLink


def test_evidence_link_persistence(tmp_path):
    db_path = tmp_path / "links.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        link = EvidenceLink(from_ref="observation:1", to_ref="event:1", relation="supports")
        session.add(link)
        session.commit()
        session.refresh(link)

        results = session.exec(select(EvidenceLink)).all()
        assert results
        assert results[0].from_ref == "observation:1"
        assert results[0].relation == "supports"
