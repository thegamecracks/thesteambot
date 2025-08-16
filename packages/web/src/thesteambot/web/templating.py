import importlib.resources

from starlette.templating import Jinja2Templates

assert __package__ is not None
package = importlib.resources.files(__package__)

templates = Jinja2Templates(directory=str(package.joinpath("templates")))
