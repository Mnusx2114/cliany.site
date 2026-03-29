from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, TabbedContent, TabPane

from cliany_site.atoms.storage import list_atoms
from cliany_site.loader import discover_adapters


class AdapterDetailScreen(Screen):
    """适配器详情界面，显示命令列表和原子视图"""

    BINDINGS = [
        ("escape", "app.pop_screen", "返回"),
        ("b", "app.pop_screen", "返回"),
    ]

    def __init__(self, domain: str, **kwargs):
        super().__init__(**kwargs)
        self.domain = domain

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="detail-container"), TabbedContent():
            with TabPane("命令", id="tab-commands"):
                yield DataTable(id="commands-table")
            with TabPane("原子", id="tab-atoms"):
                yield DataTable(id="atoms-table")
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"适配器: {self.domain}"

        commands_table = self.query_one("#commands-table", DataTable)
        atoms_table = self.query_one("#atoms-table", DataTable)

        commands_table.add_columns("名称", "描述", "步骤数", "参数")
        atoms_table.add_columns("ID", "名称", "描述", "参数数", "引用次数")

        commands_table.cursor_type = "row"
        atoms_table.cursor_type = "row"

        self._load_data()

    def _load_data(self) -> None:
        adapters = discover_adapters()
        metadata = {}
        for adapter in adapters:
            if adapter.get("domain") == self.domain:
                metadata = adapter.get("metadata", {})
                break

        commands = metadata.get("commands", [])
        atom_refs = metadata.get("atom_refs", {})

        ref_counts: dict[str, int] = {}
        for _cmd_name, refs in atom_refs.items():
            for ref in refs:
                ref_counts[ref] = ref_counts.get(ref, 0) + 1

        commands_table = self.query_one("#commands-table", DataTable)
        atoms_table = self.query_one("#atoms-table", DataTable)

        commands_table.clear()
        atoms_table.clear()

        for cmd in commands:
            name = cmd.get("name", "-")
            desc = cmd.get("description", "-")
            action_steps = cmd.get("action_steps", [])
            step_count = len(action_steps)
            args = cmd.get("args", [])
            param_names = ", ".join([a.get("name", "") for a in args]) if args else "无"
            commands_table.add_row(name, desc, str(step_count), param_names)

        atoms = list_atoms(self.domain)
        for atom in atoms:
            atom_id = atom.get("atom_id", "")
            name = atom.get("name", "")
            desc = atom.get("description", "")
            param_count = len(atom.get("parameters", []))
            ref_count = ref_counts.get(atom_id, 0)
            atoms_table.add_row(atom_id, name, desc, str(param_count), str(ref_count))
