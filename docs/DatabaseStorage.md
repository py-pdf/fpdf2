# Database storage #

## SQLAlchemy ##

The following snippet demonstrates how to store PDFs built with `fpdf2` in a database,
an then retrieve them, using [SQLAlchemy](https://www.sqlalchemy.org/):

```python
from fpdf import FPDF
from sqlalchemy import create_engine, Column, Integer, LargeBinary, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    pdf = Column(LargeBinary)

engine = create_engine('sqlite:///:memory:', echo=True)
Base.metadata.create_all(engine)

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=24)
pdf.cell(txt="My name is Bobby")
new_user = User(name="Bobby", pdf=pdf.output())

Session = sessionmaker(bind=engine)
session = Session()

session.add(new_user)

user = session.query(User).filter_by(name="Bobby").first()
with open("user.pdf", "wb") as pdf_file:
    pdf_file.write(user.pdf)
```

Note that storing large binary data in a database is usually not recommended...
You might be better off dynamically generating your PDFs from structured data in your database.
