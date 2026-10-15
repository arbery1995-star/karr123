from . import demo, kleinanzeigen

REGISTRY = {
    "kleinanzeigen": kleinanzeigen.search,
    "demo": demo.search,
}
