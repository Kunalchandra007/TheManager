"""Lambda adapter for the authenticated TheManager FastAPI application."""

from mangum import Mangum

from api.aws_app import app


handler = Mangum(app, lifespan="off")
