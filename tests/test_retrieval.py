from ragagent.retrieval.chunker import chunk_text


def test_chunk_text_respects_size_and_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, source="test.txt", chunk_size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c.text) <= 300 for c in chunks)
    assert chunks[0].source == "test.txt"
