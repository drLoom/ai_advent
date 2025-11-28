from indexing.index_manager import IndexManager
import numpy as np

manager = IndexManager()

# Test queries
queries = ["Blackwell", "revenue", "Jensen Huang", "demand for Blackwell"]

for query in queries:
    print(f"\nQuery: '{query}'")
    print("="*60)

    # Get embedding
    query_embedding = manager.embedder.generate_embedding(query)

    # Search vector store directly to see raw distances
    query_vector = np.array([query_embedding], dtype=np.float32)
    query_vector = manager.vector_store.normalize_vector(query_vector[0]).reshape(1, -1)

    distances, indices = manager.vector_store.index.search(query_vector, 3)

    print(f"Raw distances: {distances[0]}")
    print(f"Indices: {indices[0]}")

    # Calculate similarities
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx >= 0:
            dist = min(float(dist), 2.0)
            similarity = 1 - (dist ** 2 / 2)
            similarity = max(0.0, min(1.0, similarity))
            print(f"  Chunk {idx}: distance={dist:.4f}, similarity={similarity:.4f}")
