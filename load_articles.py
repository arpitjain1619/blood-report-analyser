import os

def load_articles(folder_path: str = "articles") -> list:
    """
    Reads every .md file inside each report-type subfolder of `folder_path`
    (e.g. articles/blood/, articles/lipid/) and returns a list of dicts:
        [{"filename": ..., "type": <subfolder name>, "text": ...}, ...]

    The subfolder name is the report type, which flows through to the vector
    store so retrieval can later be filtered by type (HRA-12).
    """
    articles = []
    for report_type in sorted(os.listdir(folder_path)):
        type_dir = os.path.join(folder_path, report_type)
        if not os.path.isdir(type_dir):
            continue  # skip stray files at the top level; we only read type folders
        for filename in sorted(os.listdir(type_dir)):
            if filename.endswith(".md"):
                filepath = os.path.join(type_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    articles.append({
                        "filename": filename,
                        "type": report_type,
                        "text": f.read(),
                    })
    return articles