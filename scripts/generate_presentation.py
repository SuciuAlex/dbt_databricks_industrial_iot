"""Builds the dbt + Databricks showcase deck (docs/dbt_databricks_presentation.pdf).

Command output shown on the demo slides is copied from real runs of this repo
against a Databricks SQL warehouse (catalog gea_demo); see logs/db_*.txt.
"""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "docs" / "dbt_databricks_presentation.pdf"

W, H = 960.0, 540.0
MARGIN = 54.0

NAVY = HexColor("#0B2545")
NAVY_SOFT = HexColor("#1D3B63")
ORANGE = HexColor("#FF694A")
RED = HexColor("#E8452C")
TEAL = HexColor("#0E7C7B")
GREY_BG = HexColor("#F4F6F9")
GREY_LINE = HexColor("#D6DCE5")
TEXT = HexColor("#1F2933")
MUTED = HexColor("#5B6B7C")
CODE_BG = HexColor("#0F1B2D")
CODE_TEXT = HexColor("#D8E2F0")
GREEN = HexColor("#1E9E5A")

FOOTER = "dbt + Databricks  |  GEA Industrial Telemetry showcase"


class Deck:
    def __init__(self, path):
        self.c = canvas.Canvas(str(path), pagesize=(W, H))
        self.c.setTitle("dbt + Databricks - Introduction, Options and Live Demo")
        self.page = 0

    def save(self):
        self.c.save()

    # ---------- primitives ----------

    def _footer(self):
        if self.page == 0:
            return
        self.c.setFillColor(MUTED)
        self.c.setFont("Helvetica", 8)
        self.c.drawString(MARGIN, 22, FOOTER)
        self.c.drawRightString(W - MARGIN, 22, str(self.page))

    def _end(self):
        self._footer()
        self.c.showPage()
        self.page += 1

    def _header(self, title, subtitle=None):
        self.c.setFillColor(NAVY)
        self.c.rect(0, H - 88, W, 88, stroke=0, fill=1)
        self.c.setFillColor(ORANGE)
        self.c.rect(0, H - 92, W, 4, stroke=0, fill=1)
        self.c.setFillColor(white)
        self.c.setFont("Helvetica-Bold", 24)
        self.c.drawString(MARGIN, H - 52, title)
        if subtitle:
            self.c.setFillColor(HexColor("#B9C6D8"))
            self.c.setFont("Helvetica", 11.5)
            self.c.drawString(MARGIN, H - 74, subtitle)

    def _bullets(self, items, x, y, width, size=13, leading=21, gap=9, draw=True):
        """items: list of (text, level) or plain strings. Returns the y after the last line."""
        for item in items:
            text, level = (item, 0) if isinstance(item, str) else item
            indent = x + level * 20
            bullet_font = "Helvetica-Bold" if level == 0 else "Helvetica"
            fsize = size if level == 0 else size - 1.5
            lines = simpleSplit(text, bullet_font, fsize, width - (indent - x) - 16)
            if draw:
                self.c.setFillColor(ORANGE if level == 0 else MUTED)
                self.c.setFont("Helvetica-Bold", fsize)
                self.c.drawString(indent, y, "\u2022" if level == 0 else "\u2013")
                self.c.setFillColor(TEXT if level == 0 else MUTED)
                self.c.setFont(bullet_font if level == 0 else "Helvetica", fsize)
                for i, line in enumerate(lines):
                    self.c.drawString(indent + 14, y - i * (leading - 5), line)
            y -= (leading - 5) * len(lines) + gap
        return y

    def _bullets_height(self, items, width, size=13, leading=21, gap=9):
        return 0 - self._bullets(items, 0, 0, width, size, leading, gap, draw=False)

    def _card(self, x, y, w, h, title, color=NAVY):
        self.c.setFillColor(white)
        self.c.setStrokeColor(GREY_LINE)
        self.c.setLineWidth(1)
        self.c.roundRect(x, y, w, h, 8, stroke=1, fill=1)
        self.c.setFillColor(color)
        self.c.roundRect(x, y + h - 30, w, 30, 8, stroke=0, fill=1)
        self.c.rect(x, y + h - 30, w, 16, stroke=0, fill=1)
        self.c.setFillColor(white)
        self.c.setFont("Helvetica-Bold", 12.5)
        self.c.drawString(x + 14, y + h - 20, title)

    def _code_block(self, x, y, w, h, lines, size=8.6, title=None):
        self.c.setFillColor(CODE_BG)
        self.c.roundRect(x, y, w, h, 6, stroke=0, fill=1)
        top = y + h - 18
        if title:
            self.c.setFillColor(HexColor("#7F93AD"))
            self.c.setFont("Helvetica-Bold", 8.5)
            self.c.drawString(x + 12, top, title.upper())
            top -= 14
        self.c.setFont("Courier", size)
        for line in lines:
            color = CODE_TEXT
            stripped = line.strip()
            if stripped.startswith("$"):
                color = ORANGE
            elif "PASS=" in line or "Completed successfully" in line or "[PASS" in line or "OK in" in line:
                color = HexColor("#8FE3B0")
            elif "ERROR" in line or "Failure" in line or "FAIL" in line:
                color = HexColor("#FF9C8A")
            elif stripped.startswith("=="):
                color = HexColor("#FFD48A")
            self.c.setFillColor(color)
            self.c.drawString(x + 12, top, line[:118])
            top -= size + 2.6

    # ---------- slide types ----------

    def title_slide(self, title, subtitle, meta):
        self.c.setFillColor(NAVY)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self.c.setFillColor(NAVY_SOFT)
        self.c.circle(W - 90, H - 70, 220, stroke=0, fill=1)
        self.c.setFillColor(ORANGE)
        self.c.rect(MARGIN, H - 190, 90, 6, stroke=0, fill=1)
        self.c.setFillColor(white)
        self.c.setFont("Helvetica-Bold", 40)
        self.c.drawString(MARGIN, H - 250, title)
        self.c.setFillColor(HexColor("#C7D4E5"))
        self.c.setFont("Helvetica", 17)
        for i, line in enumerate(simpleSplit(subtitle, "Helvetica", 17, W - 2 * MARGIN - 180)):
            self.c.drawString(MARGIN, H - 288 - i * 24, line)
        self.c.setFillColor(ORANGE)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(MARGIN, 70, meta)
        self._end()

    def section_slide(self, number, title, subtitle):
        self.c.setFillColor(NAVY)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self.c.setFillColor(ORANGE)
        self.c.rect(0, 0, 12, H, stroke=0, fill=1)
        self.c.setFillColor(HexColor("#40608C"))
        self.c.setFont("Helvetica-Bold", 96)
        self.c.drawString(MARGIN + 20, H / 2 - 10, number)
        self.c.setFillColor(white)
        self.c.setFont("Helvetica-Bold", 34)
        self.c.drawString(MARGIN + 190, H / 2 + 26, title)
        self.c.setFillColor(HexColor("#B9C6D8"))
        self.c.setFont("Helvetica", 14)
        for i, line in enumerate(simpleSplit(subtitle, "Helvetica", 14, W - MARGIN - 240)):
            self.c.drawString(MARGIN + 192, H / 2 - 8 - i * 20, line)
        self._end()

    def bullet_slide(self, title, subtitle, bullets, note=None):
        self.c.setFillColor(GREY_BG)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self._header(title, subtitle)
        y = self._bullets(bullets, MARGIN, H - 140, W - 2 * MARGIN)
        if note:
            self.c.setFillColor(white)
            self.c.setStrokeColor(GREY_LINE)
            self.c.roundRect(MARGIN, 52, W - 2 * MARGIN, 46, 6, stroke=1, fill=1)
            self.c.setFillColor(TEAL)
            self.c.setFont("Helvetica-Bold", 10)
            self.c.drawString(MARGIN + 14, 78, "TAKEAWAY")
            self.c.setFillColor(TEXT)
            self.c.setFont("Helvetica", 11)
            self.c.drawString(MARGIN + 14, 62, note)
        self._end()

    def two_col_slide(self, title, subtitle, left, right, note=None):
        self.c.setFillColor(GREY_BG)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self._header(title, subtitle)
        cw = (W - 2 * MARGIN - 24) / 2
        top = H - 130
        floor = 116 if note else 60
        needed = max(self._bullets_height(items, cw - 20, 11.5, 17, 6) for _, items, _ in (left, right))
        ch = min(top - floor, needed + 66)
        for i, (heading, items, color) in enumerate((left, right)):
            x = MARGIN + i * (cw + 24)
            self._card(x, top - ch, cw, ch, heading, color)
            self._bullets(items, x + 16, top - 52, cw - 20, size=11.5, leading=17, gap=6)
        if note:
            self.c.setFillColor(white)
            self.c.setStrokeColor(GREY_LINE)
            self.c.roundRect(MARGIN, 52, W - 2 * MARGIN, 46, 6, stroke=1, fill=1)
            self.c.setFillColor(TEAL)
            self.c.setFont("Helvetica-Bold", 10)
            self.c.drawString(MARGIN + 14, 78, "TAKEAWAY")
            self.c.setFillColor(TEXT)
            self.c.setFont("Helvetica", 11)
            self.c.drawString(MARGIN + 14, 62, note)
        self._end()

    def table_slide(self, title, subtitle, headers, rows, widths, note=None, highlight_col=None):
        self.c.setFillColor(GREY_BG)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self._header(title, subtitle)
        x0 = MARGIN
        y = H - 140
        total = sum(widths)
        scale = (W - 2 * MARGIN) / total
        widths = [w * scale for w in widths]

        self.c.setFillColor(NAVY_SOFT)
        self.c.rect(x0, y - 6, W - 2 * MARGIN, 26, stroke=0, fill=1)
        self.c.setFillColor(white)
        self.c.setFont("Helvetica-Bold", 10.5)
        cx = x0 + 10
        for w, head in zip(widths, headers):
            self.c.drawString(cx, y + 3, head)
            cx += w
        y -= 6

        for r, row in enumerate(rows):
            heights = []
            cells = []
            for w, cell in zip(widths, row):
                lines = simpleSplit(str(cell), "Helvetica", 9.8, w - 16)
                cells.append(lines)
                heights.append(len(lines))
            rh = max(heights) * 13 + 10
            y -= rh
            if r % 2 == 0:
                self.c.setFillColor(white)
                self.c.rect(x0, y, W - 2 * MARGIN, rh, stroke=0, fill=1)
            self.c.setStrokeColor(GREY_LINE)
            self.c.setLineWidth(0.5)
            self.c.line(x0, y, W - MARGIN, y)
            cx = x0 + 10
            for i, (w, lines) in enumerate(zip(widths, cells)):
                bold = i == 0
                self.c.setFillColor(TEXT if i != highlight_col else RED)
                self.c.setFont("Helvetica-Bold" if bold else "Helvetica", 9.8)
                for j, line in enumerate(lines):
                    self.c.drawString(cx, y + rh - 15 - j * 13, line)
                cx += w
        if note:
            self.c.setFillColor(MUTED)
            self.c.setFont("Helvetica-Oblique", 9.5)
            self.c.drawString(MARGIN, 52, note)
        self._end()

    def demo_slide(self, title, subtitle, command, output, bullets=None, caption=None):
        self.c.setFillColor(GREY_BG)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self._header(title, subtitle)

        self.c.setFillColor(HexColor("#12263F"))
        self.c.roundRect(MARGIN, H - 168, W - 2 * MARGIN, 40, 6, stroke=0, fill=1)
        self.c.setFillColor(ORANGE)
        self.c.setFont("Courier-Bold", 12)
        self.c.drawString(MARGIN + 16, H - 154, "$ " + command)

        block_h = 30 + len(output) * 11.2
        self._code_block(MARGIN, H - 182 - block_h, W - 2 * MARGIN, block_h, output,
                         title="actual output from this repo")
        if bullets:
            self._bullets(bullets, MARGIN, H - 190 - block_h - 14, W - 2 * MARGIN,
                          size=11.5, leading=17, gap=5)
        if caption:
            self.c.setFillColor(MUTED)
            self.c.setFont("Helvetica-Oblique", 9.5)
            self.c.drawString(MARGIN, 48, caption)
        self._end()

    def pipeline_slide(self, title, subtitle, stages, note):
        self.c.setFillColor(GREY_BG)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self._header(title, subtitle)
        n = len(stages)
        gap = 22
        bw = (W - 2 * MARGIN - gap * (n - 1)) / n
        card_h = 46 + max(
            sum(len(simpleSplit(it, "Helvetica", 9.6, bw - 24)) * 12 + 3 for it in items)
            for _, _, items in stages
        )
        y = 140 + ((H - 150) - 140 - card_h) / 2
        colors = [MUTED, HexColor("#B06A2C"), HexColor("#7A7A7A"), HexColor("#B8912F")]
        for i, (name, materialization, items) in enumerate(stages):
            x = MARGIN + i * (bw + gap)
            self.c.setFillColor(white)
            self.c.setStrokeColor(GREY_LINE)
            self.c.roundRect(x, y, bw, card_h, 8, stroke=1, fill=1)
            self.c.setFillColor(colors[i % len(colors)])
            self.c.roundRect(x, y + card_h - 38, bw, 38, 8, stroke=0, fill=1)
            self.c.rect(x, y + card_h - 38, bw, 20, stroke=0, fill=1)
            self.c.setFillColor(white)
            self.c.setFont("Helvetica-Bold", 14)
            self.c.drawString(x + 12, y + card_h - 18, name)
            self.c.setFont("Helvetica", 9)
            self.c.drawString(x + 12, y + card_h - 31, materialization)
            self.c.setFillColor(TEXT)
            self.c.setFont("Helvetica", 9.6)
            ty = y + card_h - 56
            for it in items:
                for line in simpleSplit(it, "Helvetica", 9.6, bw - 24):
                    self.c.drawString(x + 12, ty, line)
                    ty -= 12
                ty -= 3
            if i < n - 1:
                self.c.setFillColor(ORANGE)
                self.c.setFont("Helvetica-Bold", 18)
                self.c.drawString(x + bw + 5, y + card_h / 2 - 6, "\u203a")
        self.c.setFillColor(white)
        self.c.setStrokeColor(GREY_LINE)
        self.c.roundRect(MARGIN, 74, W - 2 * MARGIN, 52, 6, stroke=1, fill=1)
        self.c.setFillColor(TEAL)
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(MARGIN + 14, 106, "WIRED WITH ref() ONLY")
        self.c.setFillColor(TEXT)
        self.c.setFont("Helvetica", 11)
        for i, line in enumerate(simpleSplit(note, "Helvetica", 11, W - 2 * MARGIN - 28)):
            self.c.drawString(MARGIN + 14, 90 - i * 14, line)
        self._end()

    def stats_slide(self, title, subtitle, stats, bullets, note=None):
        self.c.setFillColor(GREY_BG)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        self._header(title, subtitle)
        n = len(stats)
        gap = 16
        bw = (W - 2 * MARGIN - gap * (n - 1)) / n
        y = H - 210
        for i, (value, label) in enumerate(stats):
            x = MARGIN + i * (bw + gap)
            self.c.setFillColor(white)
            self.c.setStrokeColor(GREY_LINE)
            self.c.roundRect(x, y, bw, 92, 8, stroke=1, fill=1)
            self.c.setFillColor(NAVY)
            self.c.setFont("Helvetica-Bold", 25)
            self.c.drawCentredString(x + bw / 2, y + 50, value)
            self.c.setFillColor(MUTED)
            self.c.setFont("Helvetica", 9.5)
            for j, line in enumerate(simpleSplit(label, "Helvetica", 9.5, bw - 16)):
                self.c.drawCentredString(x + bw / 2, y + 32 - j * 11, line)
        self._bullets(bullets, MARGIN, y - 36, W - 2 * MARGIN, size=12, leading=19, gap=7)
        if note:
            self.c.setFillColor(MUTED)
            self.c.setFont("Helvetica-Oblique", 9.5)
            self.c.drawString(MARGIN, 50, note)
        self._end()


def build():
    d = Deck(OUTPUT)

    # ---------------------------------------------------------------- intro
    d.title_slide(
        "dbt on Databricks",
        "What dbt is, why teams adopt it, how dbt Core and dbt Cloud compare on cost "
        "and setup effort - and a live demo on a synthetic GEA industrial telemetry fleet.",
        "GEA Industrial Telemetry Showcase  \u2022  raw \u2192 bronze \u2192 silver \u2192 gold  \u2022  800,956 synthetic IoT events",
    )

    d.bullet_slide(
        "Agenda",
        "Where we are going in the next 30 minutes",
        [
            ("1. What is dbt?", 0),
            ("The transformation layer of the modern data stack - SQL, versioned and tested", 1),
            ("2. Why use it?", 0),
            ("The concrete engineering problems it removes from a data team", 1),
            ("3. dbt on Databricks", 0),
            ("Why the combination works: Delta, Unity Catalog, elastic SQL compute", 1),
            ("4. dbt Core (CLI in your IDE) vs dbt Cloud", 0),
            ("Capabilities, licence cost and realistic setup effort for both", 1),
            ("5. Live demo on this repository", 0),
            ("Seeds, incremental builds, lineage-based selection, tests, docs - with real output", 1),
        ],
        note="Everything shown in the demo section was executed against this repo; output is copied verbatim.",
    )

    d.section_slide("01", "What is dbt?", "The 'T' in ELT - transformation as software engineering")

    d.bullet_slide(
        "dbt in one slide",
        "data build tool - an open-source transformation framework",
        [
            ("You write SELECT statements, dbt handles everything around them", 0),
            ("Each model is a .sql file containing one SELECT; dbt wraps it in the right DDL", 1),
            ("Jinja templating adds variables, macros, conditionals and reuse to plain SQL", 1),
            ("dbt compiles to native warehouse SQL and pushes execution down to Databricks", 0),
            ("No data leaves the platform - dbt orchestrates, the warehouse computes", 1),
            ("Dependencies are declared, never hardcoded", 0),
            ("ref('silver_fact_device_events') resolves to the real catalog.schema.table at runtime", 1),
            ("From those references dbt infers the full DAG and the correct execution order", 1),
            ("Tests, documentation and lineage live in the same repository as the SQL", 0),
            ("Everything is a plain text file: reviewable in pull requests, versioned in git", 1),
        ],
        note="dbt turns analytics SQL into software: modular, tested, documented and reproducible.",
    )

    d.two_col_slide(
        "Why teams adopt dbt",
        "The problems it removes, and what replaces them",
        (
            "Without dbt",
            [
                ("Hundreds of ad-hoc SQL scripts and notebooks", 0),
                ("Run order kept in someone's head or a fragile scheduler", 1),
                ("Hardcoded table names across environments", 0),
                ("Dev/prod drift, manual find-and-replace before every release", 1),
                ("Data quality checked after the complaint arrives", 0),
                ("No automated regression net when logic changes", 1),
                ("Documentation in a wiki that went stale months ago", 0),
                ("Nobody knows what breaks if a column changes", 1),
                ("Full table rebuilds because nobody trusts partial loads", 0),
            ],
            RED,
        ),
        (
            "With dbt",
            [
                ("One project, one dependency graph, one command", 0),
                ("dbt build runs models and tests in dependency order", 1),
                ("Environment-agnostic references via ref() and source()", 0),
                ("Same code promotes from dev to CI to prod unchanged", 1),
                ("Tests are declared next to the model and run every build", 0),
                ("not_null, unique, relationships, accepted_values, custom SQL", 1),
                ("Docs and lineage generated from the code itself", 0),
                ("Impact analysis before you merge, not after you break it", 1),
                ("Incremental materializations process only new data", 0),
            ],
            GREEN,
        ),
        note="The value is not 'nicer SQL' - it is engineering discipline applied to analytics.",
    )

    d.bullet_slide(
        "The building blocks you will see today",
        "Core dbt concepts used throughout this repository",
        [
            ("Models", 0),
            ("SELECT statements materialized as view, table or incremental table", 1),
            ("Seeds", 0),
            ("Small CSV files versioned in the repo and loaded with dbt seed - deterministic demo input", 1),
            ("Tests", 0),
            ("Generic tests declared in YAML plus singular tests written as SQL that must return zero rows", 1),
            ("Macros", 0),
            ("Reusable Jinja functions - this repo uses them for schema routing, batch logging and a "
             "cross-adapter day spine", 1),
            ("Materializations and hooks", 0),
            ("Incremental strategies, post-hooks for watermark maintenance and batch execution logging", 1),
            ("Packages, docs and exposures", 0),
            ("dbt_utils and dbt_expectations for extra tests; doc blocks for reusable descriptions", 1),
        ],
    )

    # ------------------------------------------------------------ databricks
    d.section_slide("02", "dbt on Databricks", "Why this specific combination")

    d.two_col_slide(
        "Why dbt and Databricks fit together",
        "Lakehouse execution plus declarative transformation",
        (
            "What Databricks brings",
            [
                ("Delta Lake tables with ACID transactions and time travel", 0),
                ("MERGE support that makes incremental models and SCD2 practical", 1),
                ("Unity Catalog governance", 0),
                ("Three-level catalog.schema.table namespace, lineage and access control", 1),
                ("Elastic SQL warehouses", 0),
                ("Scale compute per workload; serverless starts in seconds", 1),
                ("One platform for batch, streaming and ML on the same tables", 0),
            ],
            HexColor("#E8452C"),
        ),
        (
            "What dbt adds on top",
            [
                ("Structure: medallion layers enforced by folder-level configuration", 0),
                ("raw \u2192 bronze \u2192 silver \u2192 gold, each with its own schema and defaults", 1),
                ("Dependency management and safe partial rebuilds", 0),
                ("Rebuild an exact slice of the DAG instead of the whole warehouse", 1),
                ("Automated data quality gates on every run", 0),
                ("A living catalog with column-level documentation", 0),
                ("Environment promotion through profiles and targets", 0),
            ],
            NAVY,
        ),
        note="dbt never moves data - it compiles SQL that Databricks executes on your own compute.",
    )

    d.pipeline_slide(
        "The demo project architecture",
        "Synthetic GEA machine fleet: slicers, cookers, bakers and packers",
        [
            ("RAW", "4 seeds \u2022 CSV",
             ["raw_machines (20)", "raw_event_types (10)", "raw_error_codes (18)",
              "raw_device_events (800,956)", "Includes deliberate duplicates and null machine ids"]),
            ("BRONZE", "incremental",
             ["Typed and cleaned", "Deduplicated on event_id", "Null machine_id filtered out",
              "_loaded_at audit column", "Append strategy with anti-join delta filter"]),
            ("SILVER", "table / incremental",
             ["silver_dim_machines (SCD2)", "silver_fact_device_events", "silver_fact_error_events",
              "tec_ control tables: watermark, KPI mapping, batch log"]),
            ("GOLD", "views only",
             ["dim_machine_status (+ history)", "agg_machine_uptime_daily", "agg_error_analysis",
              "agg_production_output", "agg_event_frequency_minute / hour / day"]),
        ],
        "No model references a physical table name. Every hop uses ref(), so dbt can infer the complete "
        "lineage graph and rebuild any slice of it on demand.",
    )

    d.stats_slide(
        "The project by the numbers",
        "Reported by dbt itself at parse time and after a full build",
        [
            ("19", "models across bronze, silver and gold"),
            ("80", "data tests declared in YAML and SQL"),
            ("4", "seeds - deterministic CSV inputs"),
            ("800,956", "raw synthetic device events"),
            ("103", "nodes passing in a full build"),
        ],
        [
            ("Bronze reduces 800,956 raw rows to 800,691 clean rows", 0),
            ("265 rows removed: injected duplicate event_id values and rows with a null machine_id - the "
             "unique and not_null tests pass because of the transformation, not by luck", 1),
            ("silver_dim_machines holds 451 SCD2 versions for 20 machines", 0),
            ("Exactly one current row per machine, with no overlapping validity periods (enforced by a "
             "singular test)", 1),
        ],
        note="Figures captured from dbt parse and dbt build --full-refresh on the local target.",
    )

    # ---------------------------------------------------------- core vs cloud
    d.section_slide("03", "Core or Cloud?", "Two ways to run the exact same project")

    d.two_col_slide(
        "Option A: dbt Core in your IDE",
        "Open-source CLI, Apache 2.0 licence, runs anywhere Python runs",
        (
            "How it works",
            [
                ("pip install dbt-core dbt-databricks in a virtual environment", 0),
                ("Connection details live in profiles.yml with credentials from environment variables", 0),
                ("You develop in VS Code with the dbt Power User extension, git and a terminal", 0),
                ("You choose the orchestrator", 0),
                ("Databricks Workflows has a native dbt task, or use Airflow / GitHub Actions", 1),
                ("Docs are static files you host yourself", 0),
            ],
            NAVY,
        ),
        (
            "What you own",
            [
                ("Python environment and adapter version management", 0),
                ("Secret handling for warehouse tokens", 0),
                ("Scheduling, retries, alerting and run history", 0),
                ("CI pipeline: dbt build on pull requests, state comparison, artifact storage", 0),
                ("Hosting for dbt docs and the manifest", 0),
                ("Onboarding: every analyst needs a working local setup", 0),
            ],
            HexColor("#B06A2C"),
        ),
        note="Maximum control and zero licence cost - in exchange for owning the platform plumbing.",
    )

    d.two_col_slide(
        "Option B: dbt Cloud",
        "Managed development, scheduling and collaboration on top of the same dbt project",
        (
            "What you get",
            [
                ("Browser-based IDE with git guardrails - no local setup for analysts", 0),
                ("Managed job scheduler with logs, retries, notifications and run history", 0),
                ("Hosted documentation and lineage, always current", 0),
                ("CI jobs that build only modified models on a pull request", 0),
                ("Governance features on higher tiers", 0),
                ("SSO, RBAC, audit logging, dbt Mesh across multiple projects", 1),
                ("Semantic layer, catalog and Copilot code generation on paid tiers", 0),
            ],
            TEAL,
        ),
        (
            "What to check before buying",
            [
                ("Seat count: pricing is per developer seat, per month", 0),
                ("Model build volume: plans cap successful models built per month", 0),
                ("Project count: Starter allows a single project", 0),
                ("Network access from dbt Cloud to your Databricks workspace", 0),
                ("PrivateLink and IP restrictions are Enterprise+ features", 1),
                ("Where secrets and artifacts are stored under your security policy", 0),
            ],
            NAVY_SOFT,
        ),
        note="Same models, same tests, same git repo - the difference is who runs and operates it.",
    )

    d.table_slide(
        "Licence cost comparison",
        "dbt pricing published by dbt Labs, plus the Databricks compute you pay either way",
        ["Option", "Licence cost", "Included limits", "Best fit"],
        [
            ["dbt Core", "Free, Apache 2.0 open source",
             "No limits imposed by dbt; you provide the runtime and orchestration",
             "Small, technical teams comfortable owning CI/CD and scheduling"],
            ["dbt Developer", "Free",
             "1 developer seat, 3,000 successful models built per month, 1 project",
             "Individual evaluation or a single-person analytics function"],
            ["dbt Starter", "$100 per user / month",
             "5 developer seats, 15,000 models built per month, 1 project, API access",
             "A first production project with a small team and no local setup"],
            ["dbt Enterprise", "Custom pricing, billed annually",
             "100,000 models built per month, 30 projects, Mesh, advanced catalog and semantic layer",
             "Multiple domains and teams needing governance and SSO"],
            ["dbt Enterprise+", "Custom pricing",
             "Unlimited projects, PrivateLink, IP restrictions, hybrid projects",
             "Regulated environments with strict network and security requirements"],
            ["Databricks compute", "Pay per DBU plus cloud infrastructure",
             "Charged identically whether dbt Core or dbt Cloud submits the SQL",
             "Usually the dominant cost line - optimise warehouse size and auto-stop"],
        ],
        [1.0, 1.25, 2.2, 2.0],
        note="dbt plan details from getdbt.com/pricing (checked July 2026). Databricks DBU rates vary by "
             "region, cloud and warehouse type - confirm with your account team.",
    )

    d.table_slide(
        "Setup effort comparison",
        "What it actually takes to get a team productive",
        ["Dimension", "dbt Core in an IDE", "dbt Cloud"],
        [
            ["Initial environment", "Python, virtual environment, adapter install, profiles.yml and a "
                                    "personal access token per developer",
             "Log in, connect the Databricks workspace once, invite users"],
            ["Skills assumed", "Comfortable with git, terminal and Python packaging",
             "SQL and basic git; the IDE provides branch and commit guardrails"],
            ["Scheduling", "Build it: Databricks Workflows dbt task, Airflow or GitHub Actions",
             "Built-in scheduler with logs, retries and notifications"],
            ["CI on pull requests", "Write the workflow yourself, including state comparison and artifact "
                                    "handling",
             "Configure a CI job; slim builds of modified models are native"],
            ["Documentation hosting", "Generate static files and host them somewhere",
             "Hosted and refreshed automatically after each run"],
            ["Ongoing maintenance", "Version upgrades, dependency drift and runner maintenance are yours",
             "Managed by dbt Labs; you control when to adopt new releases"],
            ["Typical time to first model", "Hours per developer, plus days to build the surrounding "
                                            "CI/CD platform",
             "Minutes per developer once the workspace connection exists"],
        ],
        [0.85, 1.6, 1.4],
        note="Both options run the identical project - this repository can be executed either way without "
             "changing a single model.",
    )

    d.bullet_slide(
        "Choosing between them",
        "A pragmatic decision guide",
        [
            ("Start with dbt Core when", 0),
            ("You already run Databricks Workflows or Airflow and have CI/CD conventions in place", 1),
            ("The team is small, technical, and licence budget is constrained", 1),
            ("You want the demo running today with zero procurement", 1),
            ("Move to dbt Cloud when", 0),
            ("Analysts without local tooling need to contribute safely", 1),
            ("You need audited run history, alerting and SSO without building it", 1),
            ("Multiple teams publish interdependent projects and need Mesh-style governance", 1),
            ("A common middle path", 0),
            ("Develop with dbt Core locally, orchestrate production with the native dbt task in Databricks "
             "Workflows - no extra licence, scheduling handled by the platform you already pay for", 1),
        ],
        note="The project code is identical in all three paths; only the runtime and operations differ.",
    )

    # ------------------------------------------------------------------ demo
    d.section_slide("04", "Live demo", "Real commands, real output, from this repository")

    d.bullet_slide(
        "Demo flow",
        "Follow along in docs/dbt_presentation_demo.md",
        [
            ("1. Deterministic inputs", 0),
            ("dbt seed loads the four versioned CSV files that make up the raw layer", 1),
            ("2. A full build of the whole DAG", 0),
            ("dbt build runs 19 models and 80 tests in dependency order", 1),
            ("3. Incremental re-runs", 0),
            ("Re-running bronze with unchanged input does almost no work", 1),
            ("4. Lineage-based selection", 0),
            ("dbt build --select +model+ rebuilds an exact upstream and downstream slice", 1),
            ("5. Tests as a quality gate", 0),
            ("What a passing run looks like, and what a real failure looks like", 1),
            ("6. Documentation and lineage", 0),
            ("dbt docs generate produces a browsable catalog and DAG", 1),
            ("7. The business output", 0),
            ("Gold views queried directly on the warehouse", 1),
        ],
    )

    d.demo_slide(
        "Demo 1 - Deterministic inputs",
        "Seeds ship with the repository, so every reviewer builds the same dataset",
        "dbt seed",
        [
            "12:42:04  Found 19 models, 80 data tests, 4 seeds, 1 exposure, 1157 macros",
            "12:42:04  Concurrency: 8 threads (target='dev')",
            "",
            "12:42:10  1 of 4 START seed file raw.raw_device_events ................ [RUN]",
            "12:42:24  4 of 4 OK loaded seed file raw.raw_machines ................. [CREATE 20 in 13.56s]",
            "12:42:24  2 of 4 OK loaded seed file raw.raw_error_codes .............. [CREATE 18 in 13.56s]",
            "12:42:24  3 of 4 OK loaded seed file raw.raw_event_types .............. [CREATE 10 in 13.56s]",
            "12:53:26  1 of 4 OK loaded seed file raw.raw_device_events ............ [CREATE 800956 in 675.61s]",
            "",
            "12:53:26  Finished running 4 seeds in 0 hours 11 minutes and 22.38 seconds (682.38s).",
            "12:53:26  Completed successfully",
            "12:53:26  Done. PASS=4 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=4",
        ],
        bullets=[
            ("800,956 events, 20 machines, 10 event types and 18 error codes - generated from a fixed "
             "random seed so the dataset is reproducible on any machine", 0),
            ("The raw data deliberately contains duplicate event ids and rows with a null machine id, so "
             "the bronze layer has something real to clean", 0),
            ("Seeds are for small, versioned reference data; 800k rows over a SQL warehouse takes 11 "
             "minutes, so production volumes belong in a proper ingestion path, not in dbt seed", 0),
        ],
    )

    d.demo_slide(
        "Demo 2 - One command builds the whole DAG",
        "dbt build runs models, then their tests, in dependency order",
        "dbt build --full-refresh --threads 1",
        [
            "13:11:20  Found 19 models, 80 data tests, 4 seeds, 1 exposure, 1157 macros",
            "13:11:20  Concurrency: 1 threads (target='dev')",
            "",
            "13:12:51  36 of 103 OK created sql table model silver.silver_dim_machines ....... [OK in 3.78s]",
            "13:12:56  37 of 103 OK created sql table model silver.silver_fact_device_events . [OK in 5.23s]",
            "13:13:05  40 of 103 PASS assert_no_overlapping_scd2_periods ..................... [PASS in 1.88s]",
            "13:13:42  59 of 103 OK created sql table model silver.silver_fact_error_events .. [OK in 3.98s]",
            "13:13:49  60 of 103 OK created sql view model gold.agg_event_frequency_day ...... [OK in 7.50s]",
            "",
            "13:15:14  Finished running 1 exposure, 7 incremental models, 3 seeds, 3 table models,",
            "          80 data tests, 9 view models in 0 hours 3 minutes and 53.67 seconds (233.67s).",
            "13:15:14  Completed successfully",
            "13:15:14  Done. PASS=102 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=103",
        ],
        bullets=[
            ("dbt worked out the order: seeds first, then bronze, silver, gold - and each model's tests "
             "immediately after the model itself", 0),
            ("A single exit code tells CI whether the warehouse is in a trustworthy state", 0),
            ("Run on a Databricks Free Edition serverless SQL warehouse against the gea_demo catalog; "
             "the 800k-row seed was loaded separately beforehand", 0),
        ],
    )

    d.demo_slide(
        "Demo 3 - Incremental models make re-runs cheap",
        "Same command, unchanged input: bronze does almost no work",
        "dbt build --select tag:bronze",
        [
            "13:15:33  Found 19 models, 80 data tests, 4 seeds, 1 exposure, 1157 macros",
            "13:15:33  Concurrency: 1 threads (target='dev')",
            "",
            "13:15:52  1 of 20 OK created sql incremental model bronze.bronze_device_events . [OK in 10.33s]",
            "13:16:01  2 of 20 OK created sql incremental model bronze.bronze_error_codes ... [OK in 9.38s]",
            "13:16:11  3 of 20 OK created sql incremental model bronze.bronze_event_types ... [OK in 9.21s]",
            "13:16:20  4 of 20 OK created sql incremental model bronze.bronze_machines ...... [OK in 9.23s]",
            "13:16:43  18 of 20 PASS unique_bronze_machines_machine_id ...................... [PASS in 1.48s]",
            "",
            "13:16:46  Finished running 4 incremental models, 16 data tests in 0 hours 1 minutes",
            "          and 13.39 seconds (73.39s).",
            "13:16:46  Completed successfully",
            "13:16:46  Done. PASS=20 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=20",
        ],
        bullets=[
            ("bronze_device_events re-ran over an 800,691-row Delta table in 10.33s because its delta "
             "filter matched no new events - it inserted nothing rather than rebuilding the table", 0),
            ("The elapsed time here is dominated by per-statement round-trips to a Free Edition "
             "serverless warehouse, not by data processing", 0),
            ("The same filter is what keeps cost flat as history grows: incremental models never re-scan "
             "data they have already loaded", 0),
        ],
    )

    d.demo_slide(
        "Demo 4 - Rebuild exactly the slice you touched",
        "The + operator walks the lineage graph upstream and downstream",
        "dbt build --select +silver_fact_device_events+",
        [
            "13:16:59  Found 19 models, 80 data tests, 4 seeds, 1 exposure, 1157 macros",
            "13:16:59  Concurrency: 1 threads (target='dev')",
            "",
            "13:19:49  65 of 66 PASS accepted_values_agg_error_analysis_severity ............ [PASS in 2.17s]",
            "13:19:52  66 of 66 PASS not_null_agg_error_analysis_machine_type ............... [PASS in 1.55s]",
            "",
            "13:19:52  Finished running 3 incremental models, 2 seeds, 2 table models,",
            "          52 data tests, 7 view models in 0 hours 2 minutes and 53.80 seconds (173.80s).",
            "13:19:52  Completed successfully",
            "13:19:52  Done. PASS=66 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=66",
        ],
        bullets=[
            ("66 of the 103 nodes were selected: everything the model depends on, the model itself, and "
             "everything downstream of it - the rest were correctly left alone", 0),
            ("Nobody maintains that list by hand; it is derived from the ref() calls in the SQL", 0),
            ("Same syntax scales in CI: --select state:modified+ rebuilds only what a pull request "
             "actually changed", 0),
        ],
    )

    d.demo_slide(
        "Demo 5 - A failure stops the build, it does not leak",
        "A real defect this repository hit on Databricks, caught by dbt itself",
        "dbt build --full-refresh   # 8 threads",
        [
            "13:09:23  Completed with 2 errors, 0 partial successes, and 0 warnings:",
            "",
            "13:09:23  Failure in model agg_event_frequency_hour (models\\gold\\agg_event_frequency_hour.sql)",
            "13:09:23    Database Error in model agg_event_frequency_hour",
            "  [DELTA_CONCURRENT_APPEND.ROW_LEVEL_CHANGES] Transaction conflict detected.",
            "  A concurrent MERGE added data to table gea_demo.silver.silver_tec_watermark",
            "  committed at version 3. The concurrent operation modified the same rows that",
            "  this transaction attempted to modify. Please retry the operation.",
            "",
            "13:09:23  Done. PASS=89 WARN=0 ERROR=2 SKIP=12 NO-OP=1 TOTAL=104",
        ],
        bullets=[
            ("Three gold models share one watermark table and advance it from a post-hook, so running "
             "them in parallel makes their MERGE statements collide on the same Delta rows", 0),
            ("12 downstream nodes were skipped rather than built on top of a half-written table, and the "
             "non-zero exit code fails the pipeline", 0),
            ("Failing data tests behave exactly the same way: the run stops and names the offending "
             "model, so bad data never reaches a dashboard", 0),
        ],
        caption="Serialising the run (--threads 1) produced PASS=102 ERROR=0; the durable fix is to key the watermark by model.",
    )

    d.demo_slide(
        "Demo 6 - Documentation and lineage from the code",
        "Descriptions live in reusable doc blocks and are compiled into a catalog",
        "dbt docs generate && dbt docs serve",
        [
            "13:20:03  Running with dbt=1.11.12",
            "13:20:04  Registered adapter: databricks=1.12.2",
            "13:20:05  Found 19 models, 80 data tests, 4 seeds, 1 exposure, 1157 macros",
            "13:20:05  Concurrency: 8 threads (target='dev')",
            "",
            "13:20:11  Building catalog",
            "13:20:14  Catalog written to C:\\_REPO\\PoC\\dbt_databricks_industrial_iot\\target\\catalog.json",
        ],
        bullets=[
            ("dbt docs serve opens an interactive DAG: click any node to see its SQL, columns, tests and "
             "every downstream consumer", 0),
            ("Column descriptions are defined once in docs/column_decription.md and referenced with "
             "{{ doc('column_machine_id') }}, so the same definition appears on every layer", 0),
            ("The exposure declared for the raw layer gives the graph an explicit entry point", 0),
        ],
    )

    d.demo_slide(
        "Demo 7 - What the pipeline actually produced",
        "Querying the built warehouse directly after the run",
        "select * from gold.dim_machine_status / gold.agg_error_analysis",
        [
            "== Row counts by layer (gea_demo on Databricks) ==",
            "object                             rows",
            "raw.raw_device_events            800956",
            "bronze.bronze_device_events      800691   <- 265 dirty rows removed by bronze",
            "silver.silver_fact_device_events 800691",
            "silver.silver_dim_machines          451   <- SCD2 versions for 20 machines",
            "silver.silver_fact_error_events     100",
            "",
            "== gold.dim_machine_status (sample) ==",
            "machine_id  machine_type  status_value  plant_location  status_since",
            "BKR-001     BAKER         RUNNING       Shanghai        2026-06-26 10:05:21+00:00",
            "BKR-003     BAKER         MAINTENANCE   Bologna         2026-06-26 19:25:52+00:00",
            "CKR-001     COOKER        RUNNING       Cologne         2026-06-29 06:30:52+00:00",
            "",
            "== gold.agg_error_analysis (sample) ==",
            "machine_type  severity  error_count  avg_resolution_s  maintenance_required",
            "PACKER        LOW                12            1110.0                     0",
            "BAKER         HIGH               10           14250.0                    10",
            "COOKER        HIGH               10           21996.0                    10",
        ],
        caption="Gold views read only from silver; identical results were produced by the same code on DuckDB.",
    )

    d.bullet_slide(
        "The commands worth remembering",
        "Copy-paste cheat sheet for the audience",
        [
            ("dbt build", 0),
            ("Run every model and every test in dependency order", 1),
            ("dbt build --select +silver_fact_device_events+", 0),
            ("Rebuild one model plus all of its ancestors and descendants", 1),
            ("dbt build --select tag:gold", 0),
            ("Rebuild a single layer using folder-level tags", 1),
            ("dbt build --select state:modified+", 0),
            ("In CI, rebuild only what changed in the pull request and everything downstream", 1),
            ("dbt test / dbt compile --select <model>", 0),
            ("Run quality gates alone, or inspect the exact SQL dbt sends to Databricks", 1),
            ("dbt docs generate && dbt docs serve", 0),
            ("Publish the lineage graph and column-level catalog", 1),
        ],
        note="Full walkthrough with talking points: docs/dbt_presentation_demo.md",
    )

    d.bullet_slide(
        "Takeaways",
        "What to remember when the slides are gone",
        [
            ("dbt makes analytics SQL behave like software", 0),
            ("Versioned, reviewed, tested, documented and reproducible by anyone who clones the repo", 1),
            ("Databricks executes everything - dbt only orchestrates and compiles", 0),
            ("No data movement, no extra runtime, full use of Delta and Unity Catalog", 1),
            ("ref() is the whole trick", 0),
            ("Declared dependencies give you lineage, correct run order and surgical partial rebuilds", 1),
            ("Incremental materializations keep re-runs cheap as history grows", 0),
            ("bronze_device_events re-ran over 800,691 rows without inserting anything, because its "
             "delta filter matched no new events", 1),
            ("dbt Core costs nothing but you own the platform; dbt Cloud sells you that platform", 0),
            ("Free Developer tier, $100 per seat on Starter, custom Enterprise - the project code is "
             "identical either way", 1),
        ],
        note="Everything in this deck was run against Databricks Unity Catalog (catalog gea_demo).",
    )

    d.title_slide(
        "Questions?",
        "Repository: dbt_databricks_industrial_iot  \u2022  Demo guide: docs/dbt_presentation_demo.md  "
        "\u2022  Architecture specification: CLAUDE.md",
        "All command output in this deck was captured from real runs of this project.",
    )

    d.save()
    return OUTPUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
