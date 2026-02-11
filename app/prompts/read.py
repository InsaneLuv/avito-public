from pathlib import Path

import aiofiles


class PromptReader:
    def __init__(self, base_path: str = None):
        if base_path is None:
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent / "data"
        else:
            self.base_path = Path(base_path)

        if not self.base_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.base_path}")
        print(f"PromptReader initialized with base path: {self.base_path}")

    async def read_text(self, filename: str, subdir: str = "") -> str:
        if subdir:
            subdir = subdir.strip('/\\')
            file_path = self.base_path / subdir / filename
        else:
            file_path = self.base_path / filename

        file_path = file_path.resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            encoding = 'utf-8'
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
                return content
        except UnicodeDecodeError:
            async with aiofiles.open(file_path, 'r', encoding='cp1251') as f:
                content = await f.read()
                return content
        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {e}")
