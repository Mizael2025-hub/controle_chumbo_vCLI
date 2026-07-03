from base.modules import MenuItem, ModuleManifest, ModuleRole

MANIFEST = ModuleManifest(
    slug="chumbo",
    label="Controle de Chumbo",
    icon="chumbo",
    order=10,
    url_name="chumbo:home",
    roles=[ModuleRole.ADMIN, ModuleRole.OPERADOR],
    menu=[
        MenuItem(label="Estoque", url_name="chumbo:estoque"),
        MenuItem(label="Entrada", url_name="chumbo:lote_create", admin_only=True),
        MenuItem(label="Ligas", url_name="chumbo:ligas_list", admin_only=True),
        MenuItem(label="Destinos", url_name="chumbo:destinos_list", admin_only=True),
        MenuItem(label="Modelos", url_name="chumbo:modelos_list", admin_only=True),
    ],
    dashboard_widgets=[
        "modules.chumbo.widgets.saldo_por_liga_widget",
    ],
)
