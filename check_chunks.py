from storage.db_storage import ArticleStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Chunk

engine = create_engine('sqlite:///db/articles.sqlite')
Session = sessionmaker(bind=engine)
session = Session()

chunks = session.query(Chunk).all()
print(f"Total chunks: {len(chunks)}")
print()

for chunk in chunks:
    if 'Blackwell' in chunk.content:
        print(f"Chunk {chunk.chunk_index} (Page {chunk.page_number}):")
        print(chunk.content)
        print("\n" + "="*80 + "\n")

session.close()
