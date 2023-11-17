import os
import dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from .requests.maintainer import CreateMaintainerRequest, UpdateMaintainerRequest
from .requests.source import LoginRequest
from .services.maintainers import *
from .services.worker import Worker, WorkerManager
from .responses import make_response
from .middlewares.auth import AuthMiddleware, verify_authorization_handler, auth_error_handler
from .middlewares.contrib.auth import requires
from .services.responses.service_response import ServiceResponse
from fastapi import BackgroundTasks
from ..db.models import SourceTypeEnum
from .services.sources import *
from typing import Union

import time
from contextlib import asynccontextmanager
import multiprocessing
dotenv.load_dotenv()


manager = WorkerManager()

app = FastAPI(
    debug=os.getenv("DEBUG"),
    # lifespan=lifespan,
)


origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(
#     AuthMiddleware,
#     verify_header=verify_authorization_handler,
#     auth_error_handler=auth_error_handler
# )


@app.get("/")
async def home(request: Request):
    print("Hello")
    return {"message": "Backend manager service is up and running"}

@app.post("/maintainer/create")
@requires([])
async def create_maintainer_request_handler(request: Request, maintainer_request: CreateMaintainerRequest):
    response = await create_maintainer(maintainer_request)
    return make_response(
        status=response.response_status,
        message=response.message,
        data=response.data,
        code=response.http_code
    )

@app.post('/login')
@requires([])
async def login_request_handler(request: Request, login_request: LoginRequest):
    response = await login_maintainer(login_request)
    return make_response(
        status=response.response_status,
        message=response.message,
        data=response.data,
        code=response.http_code
    )
    
@app.get("/maintainer/{maintainer_id}")
@requires([])
async def get_maintainer_request_handler(request: Request, maintainer_id: str):
    """
        Get maintainer endpoint
    """
    response = await get_maintainer(
        maintainer_id=maintainer_id,
    )
    return make_response(
        status=response.response_status,
        message=response.message,
        data=response.data,
        code=response.http_code
    )

@app.get("/maintainers")
@requires([])
async def get_maintainers_request_handler(request: Request):
    """
        Get maintainers endpoint
    """
    response = await get_maintainers()
    return make_response(
        status=response.response_status,
        message=response.message,
        data=response.data,
        code=response.http_code
    )


@app.patch("/maintainer/{maintainer_id}")
@requires([])
async def update_maintainer_request_handler(request: Request, maintainer_id: str, updated_maintainer: UpdateMaintainerRequest):
    """
        Update maintainer account
    """
    updated_maintainer_result = await update_maintainer(
        maintainer_id,
        updated_maintainer
    )
    if updated_maintainer_result:
        return make_response(
            status='success',
            data=updated_maintainer_result,
            message='Maintainer profile updated',
        )
    return make_response(
            status='error',
            data=None,
            message='Could not update maintainer profile',
            code=400
    )


@app.post('/source/upload')
async def add_file_source_handler(
    request: Request,
    file: Union[UploadFile, None] = File(...), 
    source_name =  Form(default="source name"),
    source_description =  Form(default=""),
    source_domain =  Form(default=""),
    ):

    ## Upload file
    response = await add_file_source(
            source_name,
            source_description,
            SourceTypeEnum.File,
            source_domain,
            source_file_content=await file.read()
        )
    return make_response(
            status=response.response_status,
            message=response.message,
            data=response.data,
            code=response.http_code
        )

@app.post('/source/add')
async def add_non_file_source_handler(
    request: Request,
    source_name =  Form(default="source name"),
    source_description =  Form(default=""),
    source_type = Form(default=SourceTypeEnum.Url),
    source_url =  Form(default=""),
    source_domain =  Form(default=""),
    ):
    if source_type == SourceTypeEnum.File:
        return make_response(
            status='error',
            message='Source type not allowed',
            data=None,
            code=400
        )
    response = await add_non_file_source(
            source_name,
            source_description,
            source_type,
            source_url,
            source_domain,
        )
    return make_response(
            status=response.response_status,
            message=response.message,
            data=response.data,
            code=response.http_code
        )


@app.get('/sources')
async def get_sources_handler(
    request: Request, 
    source_type: Union[SourceTypeEnum, None] = None):
    if source_type:
        response = await get_sources_by_type(source_type)
        return make_response(
            status=response.response_status,
            message=response.message,
            data=response.data,
            code=response.http_code
        )
    response = await get_sources()
    return make_response(
            status=response.response_status,
            message=response.message,
            data=response.data,
            code=response.http_code
    )


# @app.get('/source/{source_id}')
# async def get_source():
#     pass


@app.post('/worker/create')
@requires([])
async def create_worker(request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(manager.spawn_worker, "data") ##
    return "Worker started"