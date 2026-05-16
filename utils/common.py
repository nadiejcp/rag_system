import os


def load_documents(path="documents"):
    docs = {}
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Documents directory '{path}' not found")

        for fname in os.listdir(path):
            if fname.endswith(".txt"):
                try:
                    with open(os.path.join(path, fname), "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            docs[fname] = content
                except Exception as e:
                    print(f"Error reading {fname}: {str(e)}")

        if not docs:
            raise ValueError("No valid documents found")
        return docs
    except Exception as e:
        print(f"Error loading documents: {str(e)}")
        return {}