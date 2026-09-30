load('ext://uibutton', 'cmd_button')

# Compose reads project variables from .env; .envrc is a shell script and
# must not be passed as Docker Compose's dotenv file.
if os.path.exists('.env'):
    watch_file('.env')
docker_compose('compose.tilt.yaml')
dc_resource(
    'caddy',
    links=[link('http://127.0.0.1:8000', 'Landing Page')],
)
dc_resource(
    'grist',
    new_name='Grist Spreadsheet',
    labels=['Part-1-Grist'],
    links=[
        link('http://127.0.0.1:8484', 'Grist Spreadsheet'),

    ],
)
dc_resource(
    'marimo',
    new_name='Marimo Notebook',
    labels=['Part-2-marimo'],
    links=[link('http://127.0.0.1:8081', 'Marimo Notebook')],
)

cmd_button(
    name='2-open-apiconsole',
    resource='Grist Spreadsheet',
    argv=['open', 'http://127.0.0.1:8484/apiconsole'],
    text='Open',
    icon_name='api',
)
cmd_button(
    name='1-open-grist',
    resource='Grist Spreadsheet',
    argv=['open', 'http://127.0.0.1:8484'],
    text='Open',
    icon_name='border_all',
)
cmd_button(
    name='open-marimo',
    resource='Marimo Notebook',
    argv=['open', 'http://127.0.0.1:8081'],
    text='Open',
    icon_name='notebook',
)

config.set_enabled_resources([
    'caddy',
    'Grist Spreadsheet',
    'Marimo Notebook',
])
