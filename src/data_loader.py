import json
from typing import Generator, Optional
from src.schema import RawContent

class DataLoader:
    """Streams records from the large JSON dataset."""
    
    def __init__(self, file_path: str = "data/summaries_1k.json"):
        self.file_path = file_path

    def load_samples(self, limit: Optional[int] = None) -> Generator[RawContent, None, None]:
        """
        Yields RawContent objects.
        
        Args:
            limit: Maximum number of samples to yield.
        """
        count = 0
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Load the entire JSON content
                data = json.load(f)
                
                # Handle dictionary with 'data' key or direct list
                items = []
                if isinstance(data, dict):
                    if "data" in data and isinstance(data["data"], list):
                        items = data["data"]
                    else:
                        print("Error: JSON is a dict but missing 'data' list key.")
                        return
                elif isinstance(data, list):
                    items = data
                else:
                    print(f"Error: Unknown JSON structure {type(data)}")
                    return

                for item in items:
                    if limit and count >= limit:
                        break
                    
                    yield RawContent(
                        text=item.get("markdown_content", "") or item.get("content", ""),
                        url=item.get("url"),
                        metadata={
                            "title": item.get("title"),
                            "baseline_summary": item.get("summary")
                        }
                    )
                    count += 1
        except FileNotFoundError:
            print(f"Error: {self.file_path} not found.")
        except Exception as e:
            print(f"Error loading data: {e}")
