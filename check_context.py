from indexing.index_manager import IndexManager

manager = IndexManager()
query = "What did Jensen Huang say about demand and AI?"

results = manager.search(query, top_k=3)

print(f"Query: {query}\n")
print("="*80)

for i, (metadata, score) in enumerate(results, 1):
    print(f"\nRank {i} - Score: {score:.4f}")
    print(f"Page: {metadata.get('page_number')}")
    print(f"Chunk Index: {metadata.get('chunk_index')}")
    print(f"\nFull Content:")
    print(metadata.get('content', '')[:500])  # Show more than 200
    print("\n" + "="*80)
