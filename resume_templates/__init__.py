import ast
from importlib import import_module
from pkgutil import iter_modules
from pathlib import Path


_TEMPLATES = {
    "classic": {
        "label": "Classic (current)",
        "order": 0,
        "module": None,
    }
}

for module_info in iter_modules(__path__):
    if module_info.name.startswith("_"):
        continue

    module_path = Path(__file__).with_name(f"{module_info.name}.py")
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        metadata = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in {
                        "TEMPLATE_ID",
                        "TEMPLATE_LABEL",
                        "TEMPLATE_ORDER",
                    }:
                        metadata[target.id] = ast.literal_eval(node.value)
    except (OSError, SyntaxError, TypeError, ValueError) as error:
        raise RuntimeError(f"Could not read metadata for resume template {module_info.name!r}.") from error

    template_id = metadata.get("TEMPLATE_ID")
    if template_id in _TEMPLATES:
        raise ValueError(f"Duplicate resume template id: {template_id}")
    template_label = metadata.get("TEMPLATE_LABEL")
    if (
        template_id != module_info.name
        or not isinstance(template_label, str)
        or not template_label.strip()
        or type(metadata.get("TEMPLATE_ORDER")) is not int
    ):
        raise ValueError(f"Resume template {module_info.name!r} has invalid metadata.")
    if any(details["label"] == template_label for details in _TEMPLATES.values()):
        raise ValueError(f"Duplicate resume template label: {template_label}")
    _TEMPLATES[template_id] = {
        "label": template_label,
        "order": metadata["TEMPLATE_ORDER"],
        "module": module_info.name,
    }


_SORTED_TEMPLATES = sorted(
    _TEMPLATES.items(),
    key=lambda item: (item[1]["order"], item[1]["label"]),
)


def template_options():
    return {
        details["label"]: template_id
        for template_id, details in _SORTED_TEMPLATES
    }


def generate_template(template_id, profile, education, resume, variant_id, output_path):
    template = _TEMPLATES.get(template_id)
    if template is None:
        raise ValueError(f"Unknown resume template: {template_id}")
    if template["module"] is None:
        raise ValueError("The Classic template uses the resume version's existing generator.")

    template_module = import_module(f"{__name__}.{template['module']}")
    renderer = getattr(template_module, "render_pdf", None)
    if not callable(renderer):
        raise RuntimeError(f"Resume template {template_id!r} does not define render_pdf().")
    renderer(profile, education, resume, variant_id, output_path)
