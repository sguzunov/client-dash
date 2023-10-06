import dash_glue42
from dash import Dash, Input, Output, html, dcc, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import json

# Loading clients data.
with open("data/clients.json", encoding="utf-8") as f:
    clients_data = json.load(f)

app = Dash(__name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
server = app.server
app.enable_dev_tools()

# Dropdown option that will be used to leave the current Channel.
no_channel = { "label": "No Channel", "value": "" }

def update_client_card(client):
    open_card = True
    if client is None:
        client = {}
        open_card = False

    return [
        format_client_name(client),
        "PORTFOLIO VALUE: $ {}".format(client.get("portfolioValue")),
        client.get("email"),
        client.get("phone"),
        client.get("about"),

        # Open collapsable card.
        open_card
    ]


def publish_in_channel(client_id):
    return {
        "data": {
            "clientId": client_id
        }
    }

def format_client_name(client):
    first_name = client.get("firstName")
    last_name = client.get("lastName")
    return f"{first_name} {last_name}"

def find_client(client_id):
    for client in clients_data:
        if client["id"] == client_id:
            return client
    return None

channel_selector = html.Div(id="channels-selector", className="w-25", children=[
    html.Label("Select Channel: "),
    dcc.Dropdown(id="channels-list", clearable=False),
])

client_details_card = dbc.Card(dbc.CardBody(
        [
            html.H4(id="client-name"),
            html.Div(id="client-portfolio-value"),
            html.Div(id="client-email"),
            html.Div(id="client-phone"),
            html.P(id="client-details")
        ]
    ))

# Initiate Glue42 (io.Connect) library.
app.layout = dash_glue42.Glue42(id="glue42", settings={
    "desktop": {
        "config": {
            "channels": True
        }
    }
}, children=[

    # Glue42 functionality.
    dash_glue42.Channels(id="g42-channels"),

    # UI
    html.Div(id="page-content", style={ "padding": "10px 15px" }, children=[
        html.Div(
            className="d-flex justify-content-between mb-2", 
            children=[
                html.H1("Clients"),
                channel_selector
        ]),

        # Client details card.
        dbc.Collapse(
            id="client-collapse",
            className="mb-2",
            children=client_details_card
        ),

        # Clients List
        dbc.ListGroup(
            [dbc.ListGroupItem(id=client["id"], n_clicks=0, action=True, 
                children=[
                    html.Div(format_client_name(client)),
                    html.Div("$ {}".format(client["portfolioValue"])),
            ]) for client in clients_data]
        )
    ])
])


@app.callback(
    Output("channels-selector", "style"),
    Input("glue42", "isEnterprise")
)
def channels_selector_visibility(isEnterprise):
    show_selector = (isEnterprise is None) or not isEnterprise
    visibility = "visible" if show_selector else "hidden"

    return {
        "visibility": visibility
    }


def channels_to_dpd_options(channels):
    if channels is not None:
        options = map(lambda channel: {
                      "label": channel.get('name'), "value": channel.get('name')}, channels)
        return [no_channel] + list(options)

    return [no_channel]


@app.callback(
    Output("channels-list", "options"),
    Input("g42-channels", "list")
)
def update_channels_list(channels_list):
    """Discovering all channels."""

    return channels_to_dpd_options(channels_list)


@app.callback(
    Output("g42-channels", "join"),
    Input("channels-list", "value"),
    prevent_initial_call=True
)
def join_channel(channel_name):
    """Join a channel programmatically."""

    if channel_name == no_channel["value"]:
        raise PreventUpdate

    return {
        "name": channel_name
    }


@app.callback(
    Output("g42-channels", "leave"),
    Input("channels-list", "value")
)
def leave_channel(channel_name):
    """Leave a channel programmatically."""

    if channel_name == no_channel["value"]:
        return {}

    raise PreventUpdate


@app.callback(
    Output("g42-channels", "publish"),
    [Input(client["id"], "n_clicks") for client in clients_data]
)
def handle_client_clicked(*buttons):
    """Publish the selected client to the channel's context."""

    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Button ID is mapped to the client ID.
    client_id = ctx.triggered[0]["prop_id"].split(".")[0]
    client = find_client(client_id)
    if client is None:
        raise PreventUpdate

    return publish_in_channel(client_id)


@app.callback(
    [
        Output("client-name", "children"),
        Output("client-portfolio-value", "children"),
        Output("client-email", "children"),
        Output("client-phone", "children"),
        Output("client-details", "children"),
        Output("client-collapse", "is_open")
    ],
    Input("g42-channels", "my")
)
def channel_data_changed(channel):
    print('channel', channel)
    if (channel is None) or (not ("data" in channel)) or (channel["data"] is None):
        return update_client_card(None)

    client_id = channel["data"].get("clientId")
    client = find_client(client_id)

    return update_client_card(client)


if __name__ == "__main__":
    app.run_server(debug=True, host="localhost", port="8050")
