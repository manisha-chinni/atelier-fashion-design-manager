# Atelier — Fashion Design Manager

A local-first desktop workspace for organizing fashion concepts, reviewing image classifications, tracking sustainability inputs, and preparing product and production plans.

Built with Python and PySide6, Atelier stores its catalog in SQLite and starts in **Demo Mode**. The demo uses local data and mock integrations, so you can explore the main workflow without Trello, Shopify, or model credentials.

> **Project status:** interview/demo application. The ViT inference adapter and real Trello/Shopify clients are implemented, but the visible integration actions currently use mock clients. See [What is implemented](#what-is-implemented) and [Limitations](#limitations) before using it with live accounts.

## Highlights

- Manage a searchable design catalog with category, collection, season, material, color, designer, SKU, status, and image fields.
- Upload JPG, PNG, or WEBP images and view top-K predictions, confidence, image dimensions, model name, timestamp, and inference time.
- Store sustainability inputs alongside a design and calculate a transparent **Internal Sustainability Score**.
- Create and track studio and production tasks; prepare local product drafts.
- Exercise Trello and Shopify workflows using mock clients in Demo Mode.
- Export design, sustainability, and production data to formatted Excel workbooks.
- Export editable SVG garment concepts for Illustrator-compatible asset workflows.
- Review SQLite-backed dashboard and analytics summaries.

## Screens and workflow

The application groups work into Dashboard, Design Studio, AI Classification, Sustainability, Project Tasks, Product Planning, Analytics, Integrations, and Settings.

Typical demo flow:

1. Review the seeded collection on the dashboard.
2. Add a design or upload an image for classification.
3. Save the classification as a catalog design.
4. Add sustainability details and review the internal score.
5. Create a task or prepare a product draft.
6. Try the mock Trello/Shopify actions or export an Excel workbook.

## Quick start

### Requirements

- Python 3.11 or newer
- Windows, macOS, or Linux with a graphical desktop session for the PySide6 UI
- Internet access on first real-model use if the Hugging Face checkpoint is not already cached

### Install and run

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

On macOS/Linux, activate the environment with `source .venv/bin/activate`. The application creates its data, export, and log directories on startup, initializes the SQLite schema, and seeds a small sample collection when the database is empty.

The package entry point is also available:

```bash
python -m fashion_design_manager
```

## What is implemented

| Area                 | Current behavior                                                                                                                                            |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Catalog              | Create, edit, delete, search, filter by status, select images, and view design details.                                                                     |
| Classification       | Cached Hugging Face ViT adapter for real inference; deterministic mock predictions in Demo Mode.                                                            |
| Sustainability       | Saves material, recycled/organic content, resource estimates, packaging, transport, and lifetime values. Calculates an internal planning score.             |
| Tasks                | Create tasks, assign an owner, set a due-date string, and mark tasks complete.                                                                              |
| Product planning     | Save local product records and trigger a mock Shopify draft action in Demo Mode.                                                                            |
| Trello               | Mock card workflow is wired to the UI. A separate real REST client supports boards, lists, cards, and card updates.                                         |
| Shopify              | Mock product draft workflow is wired to the UI. A separate real REST client supports product create, update, and list. Inventory update is not implemented. |
| Illustrator workflow | Generates an editable SVG concept and opens it with the system's default application. This is not Illustrator automation.                                   |
| Excel                | Creates formatted catalog, sustainability, or production workbooks with header styling, filters, widths, and frozen headers.                                |
| Dashboard            | Reads design, task, product, category, status, sustainability, and activity metrics from SQLite.                                                            |

## Architecture

```text
┌─────────────────────────┐
│       PySide6 UI        │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│      Service layer      │
└──────┬─────────────┬────┘
       │             │
┌──────▼──────┐  ┌───▼────────────────────────┐
│ SQLAlchemy  │  │ Classifier / integration    │
│ SQLite      │  │ adapters and export service │
└─────────────┘  └────────────────────────────┘
```

```text
fashion_design_manager/
├── app.py             # PySide6 application, pages, and navigation
├── classifier.py      # Cached ViT adapter and offline demo predictions
├── config.py          # Environment-driven paths and settings
├── database.py        # SQLAlchemy models, SQLite engine, and seed data
├── integrations.py    # Trello, Shopify, mock, and SVG asset clients
└── services.py        # Catalog, task, sustainability, dashboard, and Excel logic
tests/
└── test_core.py       # Focused service and mock-client tests
```

## Configuration and Demo Mode

Copy `.env.example` to `.env` and adjust the values if needed:

| Variable               | Default                       | Purpose                                                     |
| ---------------------- | ----------------------------- | ----------------------------------------------------------- |
| `FDM_DEMO_MODE`        | `true`                        | Uses offline demo predictions and mock integration actions. |
| `FDM_DATABASE`         | `data/fashion_manager.db`     | SQLite database path.                                       |
| `FDM_EXPORT_DIR`       | `exports`                     | Default export directory.                                   |
| `FDM_VIT_MODEL`        | `google/vit-base-patch16-224` | Hugging Face image-classification checkpoint.               |
| `TRELLO_API_KEY`       | empty                         | Credential read by `RealTrelloClient`.                      |
| `TRELLO_TOKEN`         | empty                         | Credential read by `RealTrelloClient`.                      |
| `SHOPIFY_STORE_URL`    | empty                         | Store host read by `RealShopifyClient`.                     |
| `SHOPIFY_ACCESS_TOKEN` | empty                         | Credential read by `RealShopifyClient`.                     |

Keep `.env` private; it is excluded by `.gitignore`. Credentials are not displayed in the UI or written to application logs. Demo Mode is suitable for exploring local catalog, task, sustainability, export, and mock integration workflows without credentials.

## Image classification

When Demo Mode is disabled (`FDM_DEMO_MODE=false`), the classifier loads the configured Hugging Face ViT model once and reuses it for subsequent predictions. PyTorch inference runs on CPU by default. The model may need to download on first use and can require significant memory.

The default checkpoint is a **pretrained generic image classifier**. Its labels are not guaranteed to be fashion-specific, and this project does not claim to have trained or fine-tuned it. In Demo Mode, predictions are deterministic mock results based on the input file and are labeled as demo output; they are not model inference.

No fine-tuning pipeline is included. To make fashion-specific claims, fine-tune on a suitable labeled dataset and report held-out evaluation results separately.

## Sustainability score

The displayed score is an internal planning heuristic, not a scientifically validated environmental metric or lifecycle assessment. Current weights are:

| Input dimension         | Weight |
| ----------------------- | -----: |
| Material sustainability |    25% |
| Recycled content        |    20% |
| Packaging               |    15% |
| Transportation          |    15% |
| Expected lifetime       |    15% |
| Production impact       |    10% |

The calculation is implemented in `sustainability_score()` in `fashion_design_manager/services.py` so it can be reviewed and adjusted.

## Integrations and asset workflow

### Trello

`MockTrelloClient` supports the no-credential demo workflow. `RealTrelloClient` contains HTTPS methods for listing boards/lists/cards and creating or updating cards. The current UI quick action is mock-backed; board selection, live account configuration, and member assignment are not wired into the desktop flow.

### Shopify

Product Planning saves product drafts locally. In Demo Mode, the Shopify action returns a mock draft. `RealShopifyClient` contains product create, update, and list operations, but the current UI does not connect that client to a live store. Inventory synchronization is not implemented because it requires Shopify location and inventory-item mapping.

### Adobe Illustrator

The Illustrator workflow exports an editable SVG garment concept to `exports/` and opens it with the system default application. Illustrator automation and automatic PNG conversion are not implemented. The SVG can be opened and further edited in Illustrator.

### Excel

The export service supports three workbook types: `catalog`, `sustainability`, and `production`. The Product Planning page exposes the catalog export button; the other workbook types can be called from `export_excel(kind, path)` in the service layer.

## Data, logs, and privacy

- SQLite database: `data/fashion_manager.db` by default.
- Excel and generated SVG assets: `exports/` by default.
- Application log: `logs/app.log`.
- Uploaded images are referenced by their selected local path; this application does not provide cloud image storage.
- `.env`, database files, exports, and logs are excluded from version control by `.gitignore`.

## Tests

Install the project dependencies, then run:

```bash
python -m pytest -q
```

The current unit tests cover design persistence, sustainability scoring, Excel workbook generation, mock integration responses, and image validation/demo classification. Interactive GUI behavior and live third-party API calls are not covered by these unit tests.

## Limitations

- The app is a local desktop demonstration, not a multi-user or audited production system.
- The offline classifier is mock behavior; the pretrained ViT checkpoint has generic labels and is not a validated fashion model.
- The sustainability score is a heuristic and should not be used for environmental claims.
- Real Trello and Shopify adapters are not connected to controls in the current UI; visible quick actions use mocks.
- Shopify inventory updates, Trello member assignment, model fine-tuning, authentication, database migrations, and background inference are not included.
- A graphical desktop session and installed PySide6 dependencies are required to launch the UI.
