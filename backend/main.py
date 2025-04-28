from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import uuid, os, datetime
from jinja2 import Environment, FileSystemLoader

app = FastAPI(title="Road Damage Reporter")

# ── Paths & database ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE_DIR, 'incidents.db')
IMAGE_DIR = os.path.join(BASE_DIR, 'images')

engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Incident(Base):
    __tablename__ = 'incidents'
    id            = Column(Integer, primary_key=True, index=True)
    timestamp     = Column(DateTime, default=datetime.datetime.utcnow)
    latitude      = Column(Float)
    longitude     = Column(Float)
    accuracy      = Column(Float)
    damage_type   = Column(String(50))
    image_filename= Column(String(200))

Base.metadata.create_all(bind=engine)
os.makedirs(IMAGE_DIR, exist_ok=True)

# Serve uploaded images
app.mount('/images', StaticFiles(directory=IMAGE_DIR), name='images')

# ── API endpoints ─────────────────────────────────────────
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
    file_path = os.path.join(IMAGE_DIR, filename)
    with open(file_path, 'wb') as img_out:
        img_out.write(await photo.read())

    session = SessionLocal()
    incident = Incident(latitude=latitude, longitude=longitude,
                        accuracy=accuracy, damage_type=damage_type,
                        image_filename=filename)
    session.add(incident)
    session.commit()
    session.refresh(incident)
    session.close()
    return {'id': incident.id, 'status': 'ok'}

@app.get('/api/incidents')
def list_incidents():
    session = SessionLocal()
    data = session.query(Incident).order_by(Incident.timestamp.desc()).all()
    session.close()
    return data

# ── Report rendering (HTML + optional PDF) ────────────────
templates = Environment(loader=FileSystemLoader(BASE_DIR))

def render_html():
    session    = SessionLocal()
    incidents  = session.query(Incident).order_by(Incident.timestamp.desc()).all()
    session.close()

    template_html = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Road Damage Report</title>
<style>
body{font-family:Arial, sans-serif;margin:40px;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #ccc;padding:8px;font-size:14px;}
img{max-width:200px;height:auto;}
</style>
</head>
<body>
<h1>Road Damage Report</h1>
<table>
<thead>
<tr><th>ID</th><th>Timestamp (UTC)</th><th>Type</th><th>Latitude</th><th>Longitude</th><th>Acc (m)</th><th>Photo</th></tr>
</thead>
<tbody>
{% for inc in incidents %}
  <tr>
    <td>{{ inc.id }}</td>
    <td>{{ inc.timestamp }}</td>
    <td>{{ inc.damage_type }}</td>
    <td>{{ '%.6f' % inc.latitude }}</td>
    <td>{{ '%.6f' % inc.longitude }}</td>
    <td>{{ '%.1f' % inc.accuracy }}</td>
    <td><img src="images/{{ inc.image_filename }}"></td>
  </tr>
{% endfor %}
</tbody>
</table>
</body>
</html>
'''
    return templates.from_string(template_html).render(incidents=incidents)

@app.get('/report', response_class=HTMLResponse)
def html_report():
    return render_html()

# PDF (requires WeasyPrint)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

@app.get('/report/pdf')
def pdf_report():
    if not WEASYPRINT_AVAILABLE:
        raise HTTPException(status_code=500, detail='WeasyPrint not installed')
    html_data = render_html()
    pdf_file  = os.path.join(BASE_DIR, 'report.pdf')
    # base_url should be the folder that *contains* the “images” directory
    HTML(string=html_data, base_url=BASE_DIR).write_pdf(pdf_file)
    return FileResponse(pdf_file, filename='road_damage_report.pdf')
