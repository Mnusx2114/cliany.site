import click


@click.command("tui")
def tui_cmd():
    """启动管理界面"""
    from cliany_site.tui.app import CliAnySiteApp

    app = CliAnySiteApp()
    app.run()
