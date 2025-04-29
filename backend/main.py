from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from openlocationcode import openlocationcode as olc
import uuid, os, datetime
from jinja2 import Environment, FileSystemLoader

app = FastAPI(title="Road Damage Reporter")

# ── Paths ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data"); os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH   = os.path.join(DATA_DIR, "incidents.db")
IMAGE_DIR = os.path.join(BASE_DIR, "images"); os.makedirs(IMAGE_DIR, exist_ok=True)

# ── Database ──────────────────────────────────────────
engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Incident(Base):
    __tablename__ = 'incidents'
    id            = Column(Integer, primary_key=True, index=True)
    timestamp     = Column(DateTime, default=datetime.datetime.utcnow)
    latitude      = Column(Float)
    longitude     = Column(Float)
    damage_type   = Column(String(50))
    image_filename= Column(String(200))
    pluscode      = Column(String(20))          # NEW

Base.metadata.create_all(bind=engine)
app.mount('/images', StaticFiles(directory=IMAGE_DIR), name='images')

# ── API ───────────────────────────────────────────────
@app.post('/api/incident')
async def create_incident(
        latitude: float = Form(...),
        longitude: float = Form(...),
        accuracy: float = Form(...),
        damage_type: str = Form(...),
        photo: UploadFile = File(...)
):
    if damage_type not in ('guardrail', 'signboard'):
        raise HTTPException(status_code=400, detail='Invalid damage_type')

    ext       = os.path.splitext(photo.filename)[1].lower() or '.jpg'
    filename  = f'{uuid.uuid4().hex}{ext}'
    with open(os.path.join(IMAGE_DIR, filename), 'wb') as out:
        out.write(await photo.read())

    pluscode = olc.encode(latitude, longitude, codeLength=10)

    db = SessionLocal()
    rec = Incident(latitude=latitude, longitude=longitude,
                   damage_type=damage_type,
                   image_filename=filename,
                   pluscode=pluscode)
    db.add(rec); db.commit(); db.refresh(rec); db.close()
    return {'id': rec.id, 'status': 'ok'}

@app.get('/api/incidents')
def list_incidents():
    db = SessionLocal()
    rows = db.query(Incident).order_by(Incident.timestamp.desc()).all()
    db.close()
    return rows

# ── Report rendering ─────────────────────────────────
templates = Environment(loader=FileSystemLoader(BASE_DIR))

def render_html():
    db   = SessionLocal()
    rows = db.query(Incident).order_by(Incident.timestamp.desc()).all()
    db.close()
    tpl = '''
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>table{border-collapse:collapse;width:100%;}th,td{border:3px solid #000;padding:8px;text-align:center;vertical-align:middle;}th{background:#f2f2f2;}img{max-width:250px;height:auto;display:block;margin:auto;}</style>
<title>Road Damage Report</title>
<style>
body{font-family:Arial, sans-serif;margin:40px;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #ccc;padding:8px;font-size:14px;}
img{max-width:200px;height:auto;}
</style></head><body>
<h1>Road Damage Report</h1>
<table>
<thead>
<tr><th>ID</th><th>Date</th><th>Type</th><th>Plus Code</th><th>Photo</th></tr>
</thead><tbody>
{% for inc in rows %}
<tr>
  <td>{{ inc.id }}</td>
  <td>{{ inc.timestamp.date() }}</td>
  <td>{{ inc.damage_type }}</td>
  <td>{{ inc.pluscode or "" }}</td>
  <td><img src="images/{{ inc.image_filename }}"></td>
</tr>
{% endfor %}
</tbody></table></body></html>
'''
    return templates.from_string(tpl).render(rows=rows)

@app.get('/report', response_class=HTMLResponse)
def html_report():
    return render_html()

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

@app.get('/report/pdf')
def pdf_report():
    if not WEASYPRINT_AVAILABLE:
        raise HTTPException(status_code=500, detail='WeasyPrint not installed')
    html = render_html()
    out  = os.path.join(BASE_DIR, 'report.pdf')
    HTML(string=html, base_url=BASE_DIR).write_pdf(out)
    return FileResponse(out, filename='road_damage_report.pdf')
