from textual.app import App
from cliany_site.tui.screens.adapter_list import AdapterListScreen


class CliAnySiteApp(App):
    """cliany-site 管理界面"""

    CSS = """
    .hidden {
        display: none;
    }
    #empty-state {
        content-align: center middle;
        height: 100%;
        color: $text-muted;
    }
    #env-status-panel {
        height: 3;
        padding: 1 2;
        background: $boost;
        color: $text;
        border-bottom: solid $primary;
    }
    #logs-container {
        height: 100%;
        overflow-y: scroll;
        padding: 1;
    }
    #logs-content {
        height: auto;
    }
    DataTable {
        height: 100%;
    }
    TabbedContent {
        height: 100%;
    }
    TabPane {
        height: 100%;
    }
    ConfirmScreen, InputPathScreen {
        align: center middle;
    }
    #confirm-dialog, #input-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }
    #confirm-buttons, #input-buttons {
        margin-top: 1;
        layout: horizontal;
        align: center middle;
    }
    #confirm-buttons Button, #input-buttons Button {
        margin: 0 1;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(AdapterListScreen())
