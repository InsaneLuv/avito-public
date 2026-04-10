from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, File, UploadFile
from starlette.responses import FileResponse

from app.core.config import AppSettings
from app.prompts.read import PromptEditor
from app.services.avito import AvitoBL

router = APIRouter()
read_router = APIRouter(tags=["Прочесть промпт"], route_class=DishkaRoute)
replace_router = APIRouter(tags=["Заменить промпт"], route_class=DishkaRoute)


@read_router.get("/prompt/{code}")
async def _(code: str, settings: FromDishka[AppSettings], editor: FromDishka[PromptEditor]):
    """
    Получение `активного` промпта по коду.
    """
    if code != settings.app.SECURITY_CODE.get_secret_value():
        return {"error": "Ошибка! Неверный код доступа"}
    file_path = editor.get_file()
    return FileResponse(path=file_path, filename='text.md', media_type='multipart/form-data')



@replace_router.put("/prompt/{code}")
async def _(code: str, settings: FromDishka[AppSettings], editor: FromDishka[PromptEditor], avito: FromDishka[AvitoBL],
            file: UploadFile = File(description="Прикрепите новый файл промпта")):
    """
    Замена `текущего` промпта новым.
    """
    if code != settings.app.SECURITY_CODE.get_secret_value():
        return {"error": "Ошибка! Неверный код доступа"}

    if not file.filename.endswith('.md') and not file.filename.endswith('.txt'):
        return {"error": "Ошибка! Файл должен быть текстовым (txt, md, и т.д.)"}

    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        await editor.write_text(text_content)
        return {
            "status": "Файл успешно загружен!",
        }

    except UnicodeDecodeError:
        return {"error": "Ошибка декодирования файла. Убедитесь, что файл в кодировке UTF-8"}
    except Exception as e:
        return {"error": f"Ошибка обработки файла: {str(e)}"}


router.include_router(replace_router)
router.include_router(read_router)
