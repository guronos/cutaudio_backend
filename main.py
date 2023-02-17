from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from moviepy.editor import AudioFileClip
import uvicorn
import shutil
from fastapi.responses import FileResponse
from starlette_validation_uploadfile import ValidateUploadFileMiddleware
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=['http://audiocut.ru/'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
]
app = FastAPI(middleware=middleware)

app.add_middleware(
        ValidateUploadFileMiddleware,
        app_path="/uploadfile/",
        max_size=15728640, #15Mbyte
)

class ConvertItem(BaseModel):
    time_begin: str
    time_end: str
    file_name: str

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    try:
        id_file=str(id(file))
        file_type = file.filename[:-5:-1] #Последние 4 символа - как правило расширение файла, копируем, для возврата файла в аналогичном расширении
        file_type = file_type[::-1]
        with open('upload/'+id_file+file_type, "wb") as wf:
            shutil.copyfileobj(file.file, wf) #Сохранение файла на сервер
            file.file.close()
        return id_file+file_type
    except ValueError:
        with open('logs/logs.txt', "a") as log:
            log.write(str(datetime.today()) + '|ErrorUPLOAD!| ' + file.filename + '\n') #Логирование ошибок
        return {'statuse':'ErrorUploadFile'}

@app.post("/convert")
async def converter(data: ConvertItem):
    try:
        audioclip = AudioFileClip('upload/'+data.file_name)
    except OSError:
        with open('logs/logs.txt', "a") as log:
            log.write(str(datetime.today()) + '|ErrorFile| ' + data.file_name + ' | ' + data.time_begin + ' | ' + data.time_end + '\n') #Логирование ошибок
        return {'status': 'ErrorFile'}
    try:
        clip = audioclip.subclip(data.time_begin, data.time_end) #Обрезка файла в заданном интервале
        clip.write_audiofile(filename='reloadclient/cut_' + data.file_name) #Ренейминг
        clip.close()
        return 'cut_' + data.file_name
    except ValueError:
        with open('logs/logs.txt', "a") as log:
            log.write(str(datetime.today()) + '|ErrorTime| ' + data.file_name + ' | ' + data.time_begin + ' | ' + data.time_end + '\n') #Логирование ошибок
        return {'status': 'ErrorConverter'}



@app.get("/download")
async def main(cut_file: str):
    try:
        some_file_path = ("reloadclient/"+cut_file)
        return FileResponse(some_file_path)
    except ValueError:
        with open('logs/logs.txt', "a") as log:
            log.write(str(datetime.today()) + '|ErrorDounloadFile| ' + cut_file + '\n') #Логирование ошибок
        return {'statuses': 'ErrorDownload'}

if __name__ == "__main__":
    uvicorn.run('main:app', host='0.0.0.0', port=5000)