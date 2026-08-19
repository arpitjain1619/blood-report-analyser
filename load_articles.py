import os

def load_articles(folder_path: str = "articles") -> dict:
    """
    Reads every .md file in the folder and returns
    {filename: file_content_as_text}
    """
    articles = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".md"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                articles[filename] = f.read()
    return articles
