"""PySide6 desktop interface."""
import logging, sys, shutil, subprocess, os
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QLabel,QPushButton,QStackedWidget,QFrame,QTableWidget,QTableWidgetItem,QHeaderView,QLineEdit,QComboBox,QFileDialog,QMessageBox,QFormLayout,QDoubleSpinBox,QSpinBox,QTextEdit,QDateEdit,QTextBrowser,QGridLayout,QScrollArea,QDialog,QDialogButtonBox)
from .config import APP_NAME, ROOT, EXPORT_DIR, DEMO_MODE, MODEL_NAME
from .database import initialize, Session, Design, Sustainability, Product, Task
from .services import list_designs, save_design, delete_design, dashboard_data, create_task, list_tasks, save_sustainability, export_excel, save_product, log_activity, safe_asset_name
from .classifier import ViTClassifier
from .integrations import MockTrelloClient, MockShopifyClient, IllustratorClient

logging.basicConfig(filename=ROOT/"logs"/"app.log",level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
classifier=ViTClassifier()
STYLE="""
QWidget { background:#f6f7f4; color:#23342d; font-family:'Segoe UI'; font-size:13px; }
QFrame#sidebar { background:#203c34; border-radius:14px; }
QLabel#brand { color:#fbf8f1; font-size:19px; font-weight:700; padding:10px; }
QPushButton#nav { text-align:left; padding:12px 14px; color:#d7e1d9; border:0; border-radius:8px; background:transparent; }
QPushButton#nav:hover,QPushButton#nav[active="true"] { background:#31564b; color:white; }
QPushButton#primary { background:#355e50; color:white; border:0; border-radius:8px; padding:10px 16px; font-weight:600; }
QPushButton#primary:hover { background:#284a3f; }
QPushButton#quiet { background:#e9eee9; color:#355e50; border:0; border-radius:8px; padding:9px 14px; }
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QDateEdit,QTextEdit { background:white; border:1px solid #dce2db; border-radius:7px; padding:8px; }
QTableWidget { background:white; border:1px solid #e2e7e1; border-radius:10px; gridline-color:#eef0ec; }
QHeaderView::section { background:#eef2ed; padding:9px; border:0; font-weight:600; color:#52665b; }
QLabel#title { font-size:26px; font-weight:650; }
QFrame#card { background:white; border:1px solid #e5e9e3; border-radius:12px; }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(APP_NAME); self.resize(1440,900); self.setMinimumSize(1100,720); self.setStyleSheet(STYLE); self.selected_design=None; self.pages={}
        root=QWidget(); layout=QHBoxLayout(root); layout.setContentsMargins(18,18,18,18); layout.setSpacing(18); self.setCentralWidget(root)
        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(230); nav=QVBoxLayout(side); nav.setContentsMargins(12,16,12,16)
        brand=QLabel("ATELIER\nFashion manager"); brand.setObjectName("brand"); nav.addWidget(brand)
        badge=QLabel("●  DEMO MODE" if DEMO_MODE else "●  LIVE WORKSPACE"); badge.setStyleSheet("color:#c8ddc4;padding:8px 12px;font-weight:700;"); nav.addWidget(badge)
        self.stack=QStackedWidget(); layout.addWidget(side); layout.addWidget(self.stack,1)
        for name,icon in [("Dashboard","◫"),("Design Studio","✳"),("AI Classification","◉"),("Sustainability","♧"),("Project Tasks","▤"),("Product Planning","□"),("Analytics","⌁"),("Integrations","↗"),("Settings","⚙")]:
            b=QPushButton(f"{icon}   {name}"); b.setObjectName("nav"); b.clicked.connect(lambda checked=False,n=name:self.navigate(n)); nav.addWidget(b); self.pages[name]=self.build_page(name)
        nav.addStretch(); self.nav_buttons=side.findChildren(QPushButton); self.navigate("Dashboard")

    def navigate(self,name):
        page=self.pages[name]; self.stack.setCurrentWidget(page)
        for b in self.nav_buttons: b.setProperty("active",name in b.text()); b.style().unpolish(b); b.style().polish(b)
        if name in ("Dashboard","Analytics"): self.refresh_dashboard(page,name)
        if name=="Design Studio": self.refresh_designs(page)
        if name=="Project Tasks": self.refresh_tasks(page)
        if name=="Sustainability": self.refresh_sustainability(page)
        if name=="Product Planning": self.refresh_products(page)

    def build_page(self,name):
        page=QWidget(); outer=QVBoxLayout(page); outer.setContentsMargins(10,4,10,8); outer.setSpacing(15)
        top=QHBoxLayout(); title=QLabel(name); title.setObjectName("title"); top.addWidget(title); top.addStretch()
        if DEMO_MODE:
            badge=QLabel("DEMO MODE · Local data + mock integrations"); badge.setStyleSheet("background:#e4ede3;color:#345748;padding:7px 11px;border-radius:8px;font-weight:600;"); top.addWidget(badge)
        outer.addLayout(top); self.stack.addWidget(page)
        if name in ("Dashboard","Analytics"):
            page.body=QVBoxLayout(); outer.addLayout(page.body)
        elif name=="Design Studio": self.design_page(page,outer)
        elif name=="AI Classification": self.classify_page(page,outer)
        elif name=="Sustainability": self.sustain_page(page,outer)
        elif name=="Project Tasks": self.tasks_page(page,outer)
        elif name=="Product Planning": self.products_page(page,outer)
        elif name=="Integrations": self.integrations_page(page,outer)
        else: self.settings_page(page,outer)
        return page

    def card(self):
        f=QFrame(); f.setObjectName("card"); l=QVBoxLayout(f); l.setContentsMargins(16,14,16,14); return f,l
    def heading(self,text,layout):
        h=QLabel(text); h.setStyleSheet("font-size:17px;font-weight:650;"); layout.addWidget(h)
    def table(self,headers,parent_layout):
        t=QTableWidget(0,len(headers)); t.setHorizontalHeaderLabels(headers); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); t.setSelectionBehavior(QTableWidget.SelectRows); t.setEditTriggers(QTableWidget.NoEditTriggers); parent_layout.addWidget(t,1); return t

    def design_page(self,page,outer):
        row=QHBoxLayout(); page.search=QLineEdit(); page.search.setPlaceholderText("Search name, category, SKU, collection…"); page.search.textChanged.connect(lambda:self.refresh_designs(page)); row.addWidget(page.search,1)
        page.filter=QComboBox(); page.filter.addItems(["All","Concept","Designing","Review","Approved","Production","Completed","Archived"]); page.filter.currentTextChanged.connect(lambda:self.refresh_designs(page)); row.addWidget(page.filter)
        add=QPushButton("＋  New design"); add.setObjectName("primary"); add.clicked.connect(self.add_design); row.addWidget(add); outer.addLayout(row)
        frame,fl=self.card(); self.heading("Design catalog",fl); page.table=self.table(["ID","Design","Category","Collection","Season","Material","Score","Status"],fl); outer.addWidget(frame,1)
        buttons=QHBoxLayout()
        for label,fn in [("Edit selected",self.edit_design),("Delete",self.remove_design),("View details",self.design_details),("Open Illustrator asset",self.open_asset)]:
            b=QPushButton(label); b.setObjectName("quiet"); b.clicked.connect(fn); buttons.addWidget(b)
        buttons.addStretch(); outer.addLayout(buttons); page.table.itemSelectionChanged.connect(lambda:self.select_design(page.table))

    def refresh_designs(self,page):
        if not hasattr(page,"table"): return
        rows=list_designs(page.search.text(),page.filter.currentText())
        page.table.setRowCount(len(rows))
        for r,d in enumerate(rows):
            vals=[d.id,d.name,d.category,d.collection,d.season,d.material,f"{d.score:.0f}",d.status]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(str(v)); item.setData(Qt.UserRole,d.id); page.table.setItem(r,c,item)
    def selected_id(self):
        p=self.pages.get("Design Studio"); return p.table.item(p.table.currentRow(),0).data(Qt.UserRole) if p and p.table.currentRow()>=0 else None
    def select_design(self,table): self.selected_design=self.selected_id()
    def add_design(self): self.design_dialog()
    def edit_design(self):
        did=self.selected_id()
        if not did: return self.warn("Select a design first.")
        with Session() as s:
            d=s.get(Design,did); data={k:getattr(d,k) for k in ["name","category","designer","collection","season","material","color","status","sku","price","image_path"]}
        self.design_dialog(data,did)
    def design_dialog(self,data=None,did=None):
        data=data or {}; dlg=QDialog(self); dlg.setWindowTitle("Edit design" if did else "New design"); form=QFormLayout(dlg); fields={}
        for key,label in [("name","Design name"),("category","Category"),("designer","Designer"),("collection","Collection"),("season","Season"),("material","Material"),("color","Color"),("sku","SKU")]:
            w=QLineEdit(str(data.get(key,""))); fields[key]=w; form.addRow(label,w)
        status=QComboBox(); status.addItems(["Concept","Designing","Review","Approved","Production","Completed","Archived"]); status.setCurrentText(data.get("status","Concept")); fields["status"]=status; form.addRow("Status",status)
        price=QDoubleSpinBox(); price.setMaximum(100000); price.setPrefix("$ "); price.setValue(float(data.get("price",0) or 0)); fields["price"]=price; form.addRow("Price",price)
        image=QLineEdit(data.get("image_path", "")); browse=QPushButton("Choose image…"); browse.clicked.connect(lambda:image.setText(QFileDialog.getOpenFileName(dlg,"Select image",filter="Images (*.png *.jpg *.jpeg *.webp)")[0] or image.text())); box=QHBoxLayout(); box.addWidget(image); box.addWidget(browse); form.addRow("Image",box); fields["image_path"]=image
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); buttons.accepted.connect(dlg.accept); buttons.rejected.connect(dlg.reject); form.addRow(buttons)
        if dlg.exec():
            values={k:(w.currentText() if isinstance(w,QComboBox) else w.value() if isinstance(w,QDoubleSpinBox) else w.text()) for k,w in fields.items()}
            if not values["name"].strip(): return self.warn("Design name is required.")
            save_design(values,did); self.refresh_designs(self.pages["Design Studio"])
    def remove_design(self):
        did=self.selected_id()
        if not did: return self.warn("Select a design first.")
        delete_design(did); self.refresh_designs(self.pages["Design Studio"])
    def design_details(self):
        did=self.selected_id()
        if not did:return self.warn("Select a design first.")
        with Session() as s:
            d=s.get(Design,did); sustainability=d.sustainability
            msg=f"<h2>{d.name}</h2><p>{d.category} · {d.collection} · {d.season}</p><p>Material: {d.material} | Color: {d.color}</p><p>Status: {d.status} | Designer: {d.designer}</p><p>AI: {d.prediction or 'Not analyzed'} ({d.confidence:.1%})</p><p>Internal Sustainability Score: {d.score:.0f}/100</p>"
            if sustainability: msg+=f"<p>Source: {sustainability.source}; recycled {sustainability.recycled:.0f}%; packaging: {sustainability.packaging}; transport: {sustainability.transport}</p>"
            if d.image_path and Path(d.image_path).exists(): msg+=f'<img src="{Path(d.image_path).as_uri()}" width="380">'
        box=QMessageBox(self); box.setWindowTitle("Design details"); box.setTextFormat(Qt.RichText); box.setText(msg); box.exec()
    def open_asset(self):
        did=self.selected_id()
        if not did:return self.warn("Select a design first.")
        with Session() as s: d=s.get(Design,did); name,color,cat=d.name,d.color,d.category
        from .config import ROOT
        asset=ROOT/"exports"/(safe_asset_name(name)+".svg"); IllustratorClient.export_svg(name,cat,color,str(asset)); self.open_file(asset)

    def classify_page(self,page,outer):
        row=QHBoxLayout(); left,_=self.card(); ll=left.layout(); self.heading("Image analysis",ll); page.image=QLabel("Drop into the studio\n\nChoose a garment image to begin"); page.image.setAlignment(Qt.AlignCenter); page.image.setMinimumSize(390,350); page.image.setStyleSheet("background:#f1f2ec;color:#819087;border-radius:10px;"); ll.addWidget(page.image)
        choose=QPushButton("Choose fashion image"); choose.setObjectName("primary"); choose.clicked.connect(lambda:self.choose_classification(page)); ll.addWidget(choose); row.addWidget(left,1)
        right,_=self.card(); rl=right.layout(); self.heading("Prediction",rl); page.result=QTextBrowser(); page.result.setHtml("<p style='color:#748179'>Your model output will appear here.</p>"); rl.addWidget(page.result,1)
        page.save_btn=QPushButton("Save as design"); page.save_btn.setObjectName("primary"); page.save_btn.setEnabled(False); page.save_btn.clicked.connect(lambda:self.save_classification(page)); rl.addWidget(page.save_btn); row.addWidget(right,1); outer.addLayout(row,1)
        page.upload=""
    def choose_classification(self,page):
        path=QFileDialog.getOpenFileName(self,"Select image",filter="Images (*.png *.jpg *.jpeg *.webp)")[0]
        if not path:return
        try:
            output=classifier.predict_top_k(path,5,demo=DEMO_MODE); page.upload=path; pix=QPixmap(path); page.image.setPixmap(pix.scaled(page.image.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
            pred=output["predictions"]; page.output=output; page.result.setHtml(f"<h2>{pred[0][0]}</h2><p style='font-size:24px;color:#355e50'>{pred[0][1]:.1%} confidence</p>"+"".join(f"<p>{i+1}. {name} <b>{prob:.1%}</b></p>" for i,(name,prob) in enumerate(pred))+f"<hr><p>{output['model']}</p><p>{output['dimensions'][0]} × {output['dimensions'][1]} · {output['elapsed']:.2f}s</p><p>{output['timestamp']}</p>"); page.save_btn.setEnabled(True)
        except Exception as exc: logging.exception("Classification failed"); self.warn(str(exc))
    def save_classification(self,page):
        out=page.output; name=Path(page.upload).stem.replace("_"," ").title(); pred=out["predictions"][0]
        save_design({"name":name,"category":pred[0],"image_path":page.upload,"prediction":pred[0],"confidence":pred[1]}); self.notice("Design saved to the catalog.")

    def sustain_page(self,page,outer):
        frame,layout=self.card(); form=QFormLayout(); page.design=QComboBox(); form.addRow("Design",page.design)
        page.fields={}
        for key,label in [("source","Material source"),("recycled","Recycled content %"),("organic","Organic content %"),("water","Estimated water usage (L)"),("energy","Estimated energy usage (kWh)"),("packaging","Packaging type"),("recyclable","Packaging recyclability %"),("transport","Transportation"),("lifetime","Expected lifetime (years)")]:
            if key in ("recycled","organic","water","energy","recyclable","lifetime"):
                w=QDoubleSpinBox(); w.setMaximum(100000); w.setValue(50 if key=="lifetime" else 0); w.setSuffix("%" if key in ("recycled","organic","recyclable") else "")
            elif key=="transport": w=QComboBox(); w.addItems(["Rail","Sea","Road","Air","Local"])
            else: w=QLineEdit()
            page.fields[key]=w; form.addRow(label,w)
        layout.addLayout(form); page.score=QLabel("Internal Sustainability Score — enter values and save"); page.score.setStyleSheet("font-size:20px;font-weight:650;color:#355e50;"); layout.addWidget(page.score)
        weights=QLabel("Method: material 25% · recycled content 20% · packaging 15% · transport 15% · lifetime 15% · production impact 10%. Internal planning heuristic; not a validated environmental metric."); weights.setWordWrap(True); layout.addWidget(weights)
        b=QPushButton("Save sustainability profile"); b.setObjectName("primary"); b.clicked.connect(lambda:self.save_sustain(page)); layout.addWidget(b); outer.addWidget(frame); page.record_table=self.table(["Design","Material","Recycled","Packaging","Transport","Score"],outer)
    def refresh_sustainability(self,page):
        if not hasattr(page,"design"):return
        ds=list_designs(); page.design.clear()
        for d in ds: page.design.addItem(f"{d.id} · {d.name}",d.id)
        with Session() as s: rows=s.query(Sustainability).all()
        page.record_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([x.design.name,x.design.material,f"{x.recycled:.0f}%",x.packaging,x.transport,f"{x.score:.0f}"]): page.record_table.setItem(r,c,QTableWidgetItem(str(v)))
    def save_sustain(self,page):
        did=page.design.currentData()
        if not did:return self.warn("Add a design first.")
        values={k:(w.currentText() if isinstance(w,QComboBox) else w.value() if isinstance(w,QDoubleSpinBox) else w.text()) for k,w in page.fields.items()}
        score=save_sustainability(did,values); page.score.setText(f"Internal Sustainability Score  ·  {score}/100"); self.refresh_sustainability(page)

    def tasks_page(self,page,outer):
        row=QHBoxLayout(); page.title=QLineEdit(); page.title.setPlaceholderText("e.g. Approve fabric swatches"); row.addWidget(page.title,1); page.assignee=QLineEdit(); page.assignee.setPlaceholderText("Owner"); row.addWidget(page.assignee); page.due=QLineEdit(); page.due.setPlaceholderText("Due date YYYY-MM-DD"); row.addWidget(page.due); b=QPushButton("＋ Add task"); b.setObjectName("primary"); b.clicked.connect(lambda:self.add_task(page)); row.addWidget(b); outer.addLayout(row); frame,l=self.card(); self.heading("Production & project tasks",l); page.table=self.table(["Task","Design","Owner","Due date","Status"],l); outer.addWidget(frame,1)
        done=QPushButton("Mark selected complete"); done.setObjectName("quiet"); done.clicked.connect(lambda:self.mark_task(page)); outer.addWidget(done)
    def add_task(self,page):
        if not page.title.text().strip():return self.warn("Enter a task title.")
        create_task(page.title.text(),page.assignee.text() or "Studio team",page.due.text()); page.title.clear(); self.refresh_tasks(page)
    def refresh_tasks(self,page):
        if not hasattr(page,"table"):return
        rows=list_tasks(); page.table.setRowCount(len(rows))
        for r,t in enumerate(rows):
            vals=[t.title,t.design.name if t.design else "—",t.assignee,t.due_date,t.status]
            for c,v in enumerate(vals): page.table.setItem(r,c,QTableWidgetItem(str(v)))
    def mark_task(self,page):
        r=page.table.currentRow()
        if r<0:return self.warn("Select a task first.")
        task_id=list_tasks()[r].id
        with Session() as s: t=s.get(Task,task_id); t.status="Done"; s.commit()
        self.refresh_tasks(page)

    def products_page(self,page,outer):
        row=QHBoxLayout(); page.design=QComboBox(); row.addWidget(page.design,1); page.title=QLineEdit(); page.title.setPlaceholderText("Product title"); row.addWidget(page.title,2); page.sku=QLineEdit(); page.sku.setPlaceholderText("SKU"); row.addWidget(page.sku); page.price=QDoubleSpinBox(); page.price.setMaximum(100000); page.price.setPrefix("$ "); row.addWidget(page.price); page.stock=QSpinBox(); page.stock.setMaximum(999999); page.stock.setPrefix("Qty "); row.addWidget(page.stock); outer.addLayout(row)
        page.description=QTextEdit(); page.description.setPlaceholderText("Product description · materials · care notes"); page.description.setMaximumHeight(100); outer.addWidget(page.description)
        buttons=QHBoxLayout()
        for text,fn in [("Save draft",lambda:self.product_action(page,"draft")),("Create Shopify product",lambda:self.product_action(page,"shopify")),("Export catalog",lambda:self.export("catalog")),("Create Trello task",lambda:self.product_action(page,"trello"))]:
            b=QPushButton(text); b.setObjectName("primary" if "Shopify" in text else "quiet"); b.clicked.connect(fn); buttons.addWidget(b)
        buttons.addStretch(); outer.addLayout(buttons); page.table=self.table(["Product","SKU","Price","Inventory","Platform"],outer)
    def refresh_products(self,page):
        if not hasattr(page,"design"):return
        page.design.clear()
        for d in list_designs(): page.design.addItem(f"{d.id} · {d.name}",d.id)
        with Session() as s: rows=s.query(Product).all()
        page.table.setRowCount(len(rows))
        for r,p in enumerate(rows):
            for c,v in enumerate([p.title,p.sku,f"${p.price:.2f}",p.inventory,p.platform_id or "Local draft"]):page.table.setItem(r,c,QTableWidgetItem(str(v)))
    def product_action(self,page,action):
        did=page.design.currentData(); title=page.title.text().strip()
        if not did or not title:return self.warn("Choose a design and enter a product title.")
        sku=page.sku.text() or f"AT-{did:04d}"; product={"title":title,"body_html":page.description.toPlainText(),"variants":[{"price":str(page.price.value()),"sku":sku,"inventory_quantity":page.stock.value()}],"status":"draft"}
        platform=""
        if action=="shopify":
            result=MockShopifyClient().create_product(product); platform=result["id"]
        if action=="trello":
            result=MockTrelloClient().create_card("Product planning · "+title,page.description.toPlainText()); self.notice(f"Mock Trello card created: {result['id']}")
        save_product(did,title,sku,page.description.toPlainText(),page.price.value(),page.stock.value(),platform); self.refresh_products(page)
        if action=="shopify": self.notice(f"Mock Shopify draft created: {platform} (Demo Mode).")

    def integrations_page(self,page,outer):
        intro=QLabel("External services use replaceable clients. Demo Mode routes actions to local mock clients; no external service is contacted."); intro.setWordWrap(True); outer.addWidget(intro)
        grid=QGridLayout(); outer.addLayout(grid)
        for idx,(title,detail,fn) in enumerate([("Trello","Create a production card in the demo board.",self.trello_demo),("Shopify","Create a local mock product draft.",lambda:self.navigate("Product Planning")),("Illustrator workflow","Export an editable SVG garment concept and PNG preview.",self.illustrator_demo),("Excel","Export design, sustainability, or production workbook.",lambda:self.export("catalog"))]):
            f,l=self.card(); self.heading(title,l); desc=QLabel(detail); desc.setWordWrap(True); l.addWidget(desc); b=QPushButton("Run demo workflow"); b.setObjectName("quiet"); b.clicked.connect(fn); l.addWidget(b); grid.addWidget(f,idx//2,idx%2)
    def trello_demo(self):
        ds=list_designs()
        if not ds:return self.warn("Create a design first.")
        card=MockTrelloClient().create_card("Production: Spring 2027 · "+ds[0].name); self.notice(f"Mock Trello card created · {card['id']}")
    def illustrator_demo(self):
        ds=list_designs()
        if not ds:return self.warn("Create a design first.")
        d=ds[0]; path=ROOT/"exports"/(safe_asset_name(d.name)+".svg"); IllustratorClient.export_svg(d.name,d.category,d.color,str(path)); self.open_file(path)

    def settings_page(self,page,outer):
        frame,layout=self.card(); self.heading("Workspace settings",layout); form=QFormLayout(); mode=QLabel("ON · Demo Mode" if DEMO_MODE else "OFF · Live integrations available"); form.addRow("Mode",mode); form.addRow("Database",QLabel(str(ROOT/"data"/"fashion_manager.db"))); form.addRow("Export directory",QLabel(str(EXPORT_DIR))); form.addRow("ViT model",QLabel(MODEL_NAME)); layout.addLayout(form)
        note=QLabel("Secrets are loaded from environment variables / .env and are never shown in this screen or logs. Configure TRELLO_API_KEY, TRELLO_TOKEN, SHOPIFY_STORE_URL, and SHOPIFY_ACCESS_TOKEN."); note.setWordWrap(True); layout.addWidget(note); b=QPushButton("Open exports folder"); b.setObjectName("quiet"); b.clicked.connect(lambda:self.open_file(EXPORT_DIR)); layout.addWidget(b); outer.addWidget(frame)
    def refresh_dashboard(self,page,name):
        if not hasattr(page,"body"):return
        layout=page.body
        while layout.count(): item=layout.takeAt(0); w=item.widget(); w.deleteLater() if w else None
        data=dashboard_data(); grid=QGridLayout()
        metrics=[("Total designs",data["designs"]),("AI analyzed",data["analyzed"]),("Average sustainability",f"{data['avg_score']}/100"),("Sustainable designs",data["sustainable"]),("Active tasks",data["tasks"]),("Product drafts",data["products"])]
        for i,(label,val) in enumerate(metrics):
            f,l=self.card(); small=QLabel(label.upper()); small.setStyleSheet("color:#708076;font-size:11px;font-weight:700;"); big=QLabel(str(val)); big.setStyleSheet("font-size:28px;font-weight:700;color:#29463b;"); l.addWidget(small); l.addWidget(big); grid.addWidget(f,i//3,i%3)
        layout.addLayout(grid)
        lower=QHBoxLayout(); f,l=self.card(); self.heading("Collection at a glance",l)
        if name=="Analytics":
            for section,counts in [("Design status",data["statuses"]),("Category mix",data["categories"])]:
                self.heading(section,l)
                for key,val in counts.items():
                    line=QLabel(f"{key:<22} {'▰'*min(20,val*3)}  {val}"); line.setStyleSheet("color:#476354;padding:4px;"); l.addWidget(line)
        else:
            for key,val in data["statuses"].items(): l.addWidget(QLabel(f"{key}   ·   {val} designs"))
            l.addSpacing(10); self.heading("Category mix",l)
            for key,val in data["categories"].items(): l.addWidget(QLabel(f"{key}   ·   {val}"))
        l.addStretch(); lower.addWidget(f,1)
        f2,l2=self.card(); self.heading("Recent studio activity",l2)
        for a in data["activities"]: l2.addWidget(QLabel(f"•  {a.message}"))
        if not data["activities"]: l2.addWidget(QLabel("No recent activity yet"))
        l2.addStretch(); lower.addWidget(f2,1); layout.addLayout(lower,1)
        b=QPushButton("＋ Add a design"); b.setObjectName("primary"); b.clicked.connect(lambda:self.navigate("Design Studio")); layout.addWidget(b,alignment=Qt.AlignLeft)
    def export(self,kind):
        path=QFileDialog.getSaveFileName(self,"Export workbook",str(EXPORT_DIR/f"{kind}.xlsx"),"Excel workbook (*.xlsx)")[0]
        if path:
            try: export_excel(kind,path); self.notice(f"Workbook exported to {path}")
            except Exception as exc: logging.exception("Excel export failed"); self.warn(f"Could not export workbook: {exc}")
    def open_file(self,path):
        try: os.startfile(str(path))
        except Exception:
            try: subprocess.Popen(["explorer",str(path)])
            except Exception as exc:self.warn(f"Could not open file: {exc}")
    def notice(self,msg): QMessageBox.information(self,"Atelier",msg)
    def warn(self,msg): QMessageBox.warning(self,"Atelier",msg)

def main():
    initialize(); logging.info("Application started; demo_mode=%s",DEMO_MODE); app=QApplication(sys.argv); app.setApplicationName(APP_NAME); w=MainWindow(); w.show(); sys.exit(app.exec())
