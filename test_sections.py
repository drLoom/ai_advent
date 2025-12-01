from storage.models import Chunk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///db/articles.sqlite')
Session = sessionmaker(bind=engine)
session = Session()

chunks = session.query(Chunk).limit(10).all()

print(f"Total chunks in database: {session.query(Chunk).count()}\n")
print("First 10 chunks:\n" + "="*80 + "\n")

for chunk in chunks:
    print(f"Chunk {chunk.chunk_index}:")
    print(f"  Section: {chunk.section_title}")
    print(f"  Tokens: {chunk.token_count}")
    print(f"  Content preview: {chunk.content[:100]}...")
    print()

# Count chunks with section titles
with_sections = session.query(Chunk).filter(
    Chunk.section_title != None
).count()

print(f"\nChunks with section titles: {with_sections}")

session.close()
