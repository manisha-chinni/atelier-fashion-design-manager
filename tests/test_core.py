import tempfile
from pathlib import Path
from fashion_design_manager.config import ROOT
from PIL import Image
from fashion_design_manager.classifier import ViTClassifier
from fashion_design_manager.services import sustainability_score, export_excel
from fashion_design_manager.integrations import MockTrelloClient, MockShopifyClient
from fashion_design_manager.database import initialize, Session, Design
from fashion_design_manager.services import save_design, delete_design

def test_design_create_and_retrieve():
    initialize()
    design_id=save_design({"name":"Test garment","category":"Jacket","status":"Concept"})
    with Session() as session:
        design=session.get(Design,design_id)
        assert design and design.name=="Test garment"
    delete_design(design_id)

def test_sustainability_score_bounds():
    assert 0 <= sustainability_score(50,50,80,"Rail",5,100,10) <= 100
    assert sustainability_score(90,90,95,"Rail",5,20,4) > sustainability_score(0,0,0,"Air",1,500,100)

def test_mock_integrations():
    assert MockTrelloClient().create_card("test")["id"].startswith("DEMO-")
    assert MockShopifyClient().create_product({"title":"test"})["status"] == "draft"

def test_image_validation_and_demo_prediction():
    (ROOT/".test-tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/".test-tmp") as folder:
        good=Path(folder)/"garment.png"; Image.new("RGB",(64,80),(90,120,100)).save(good)
        out=ViTClassifier().predict_top_k(good,3,demo=True)
        assert len(out["predictions"])==3 and out["dimensions"]==(64,80) and out["demo"]
        bad=Path(folder)/"invalid.jpg"; bad.write_text("not an image")
        try: ViTClassifier().predict_top_k(bad,demo=True)
        except ValueError: pass
        else: raise AssertionError("Invalid image must be rejected")

def test_excel_export():
    initialize()
    (ROOT/".test-tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/".test-tmp") as folder:
        path=export_excel("catalog",Path(folder)/"catalog.xlsx")
        assert path.exists() and path.stat().st_size > 1000
