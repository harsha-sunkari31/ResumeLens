from fastapi import FastAPI, UploadFile, File, Form,Request
from fastapi.responses import HTMLResponse
from pypdf import PdfReader
from docx import Document
import os
import shutil
import re 
from fastapi.templating import Jinja2Templates

app = FastAPI(title="ResumeLens")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

skills_list = [
    "python", "java", "c", "c++", "sql", "mysql",
    "mongodb", "html", "css", "javascript", "react",
    "node.js", "django", "flask", "fastapi", "pandas",
    "numpy", "matplotlib", "machine learning",
    "deep learning", "artificial intelligence", "nlp",
    "power bi", "tableau", "excel", "git", "github",
    "docker", "aws"
]


def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def read_docx(file_path):
    document = Document(file_path)
    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def read_resume(file_path):

    if file_path.lower().endswith(".pdf"):
        return read_pdf(file_path)

    if file_path.lower().endswith(".docx"):
        return read_docx(file_path)

    return ""


def find_skills(text):
    text = text.lower()
    found = []

    for skill in skills_list:
        if skill in text:
            found.append(skill)

    return sorted(set(found))


def find_email(text):

    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    result = re.search(pattern, text)

    if result:
        return result.group()

    return "Not found"


def find_phone(text):

    pattern = r"(?:\+91[\s-]?)?[6-9]\d{9}"

    result = re.search(pattern, text)

    if result:
        return result.group()

    return "Not found"

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resume_text = read_resume(file_path)

    if not resume_text:
        return """
        <h2>
        Please upload a PDF or DOCX resume.
        </h2>

        <a href="/">Go Back</a>
        """

    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_description)

    matched_skills = list(
        set(resume_skills) & set(job_skills)
    )

    missing_skills = list(
        set(job_skills) - set(resume_skills)
    )

    if len(job_skills) > 0:
        skill_score = (
            len(matched_skills) / len(job_skills)
        ) * 100
    else:
        skill_score = 0

    ats_score = skill_score

    if find_email(resume_text) != "Not found":
        ats_score += 5

    if find_phone(resume_text) != "Not found":
        ats_score += 5

    sections = [
        "education",
        "skills",
        "projects",
        "experience"
    ]

    for section in sections:
        if section in resume_text.lower():
            ats_score += 5

    ats_score = min(round(ats_score), 100)

    matched_html = ""

    for skill in matched_skills:
        matched_html += f"<li>{skill}</li>"

    missing_html = ""

    for skill in missing_skills:
        missing_html += f"<li>{skill}</li>"

    resume_html = ""

    for skill in resume_skills:
        resume_html += f"<li>{skill}</li>"

    return f"""

    <!DOCTYPE html>

    <html>

    <head>

        <title>ResumeLens Results</title>

        <style>

            body {{
                font-family: Arial;
                background: #f2f4f7;
                padding: 30px;
            }}

            .container {{
                max-width: 900px;
                margin: auto;
                background: white;
                padding: 35px;
                border-radius: 15px;
            }}

            h1 {{
                text-align: center;
            }}

            .score {{
                text-align: center;
                font-size: 50px;
                font-weight: bold;
                margin: 30px;
            }}

            .box {{
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 20px;
                margin-top: 20px;
            }}

            li {{
                margin: 8px;
            }}

            a {{
                display: block;
                margin-top: 30px;
                text-align: center;
            }}

        </style>

    </head>

    <body>

        <div class="container">

            <h1>ResumeLens</h1>

            <div class="score">
                ATS Score: {ats_score}/100
            </div>

            <div class="box">

                <h2>Candidate Details</h2>

                <p>
                    <b>Email:</b>
                    {find_email(resume_text)}
                </p>

                <p>
                    <b>Phone:</b>
                    {find_phone(resume_text)}
                </p>

            </div>

            <div class="box">

                <h2>Skills Found in Resume</h2>

                <ul>
                    {resume_html}
                </ul>

            </div>

            <div class="box">

                <h2>Matched Skills</h2>

                <ul>
                    {matched_html}
                </ul>

                <p>
                    Skill Match: {round(skill_score)}%
                </p>

            </div>

            <div class="box">

                <h2>Missing Skills</h2>

                <ul>
                    {missing_html}
                </ul>

            </div>

            <div class="box">

                <h2>Recommendations</h2>

                <ul>

                    <li>
                        Add missing technical skills if you actually know them.
                    </li>

                    <li>
                        Add strong projects related to the job.
                    </li>

                    <li>
                        Use measurable achievements in your resume.
                    </li>

                    <li>
                        Customize your resume according to the job description.
                    </li>

                </ul>

            </div>

            <a href="/">
                Analyze Another Resume
            </a>

        </div>

    </body>

    </html>
    """


# ---------- START WEBSITE ----------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )