"""CI guard against adding unauthenticated Flask mutation routes."""

import ast
from pathlib import Path


ROUTES_DIR = Path(__file__).parents[1] / "app" / "routes"
UNAUTHENTICATED_BOOTSTRAP = {
    ("auth.py", "store_registration_token"),
    ("auth.py", "complete_registration"),
    ("auth.py", "social_auth_register"),
    ("auth.py", "set_password_social"),
    ("auth.py", "register"),
    ("auth.py", "login"),
    ("auth.py", "social_auth"),
    ("auth.py", "request_password_reset"),
    ("auth.py", "reset_password"),
}
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _route_methods(decorator):
    if not isinstance(decorator, ast.Call):
        return set()
    attribute = decorator.func
    if not isinstance(attribute, ast.Attribute):
        return set()
    if attribute.attr in {"post", "put", "patch", "delete"}:
        return {attribute.attr.upper()}
    if attribute.attr != "route":
        return set()
    for keyword in decorator.keywords:
        if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
            return {
                item.value.upper()
                for item in keyword.value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            }
    return set()


def test_every_non_bootstrap_mutation_route_requires_jwt():
    violations = []
    for path in sorted(ROUTES_DIR.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            methods = set().union(*(_route_methods(item) for item in node.decorator_list))
            if not methods.intersection(MUTATION_METHODS):
                continue
            if (path.name, node.name) in UNAUTHENTICATED_BOOTSTRAP:
                continue
            decorators = {ast.unparse(item) for item in node.decorator_list}
            if not any("jwt_required" in item for item in decorators):
                violations.append(f"{path.name}:{node.lineno} {node.name}")

    assert not violations, "Mutation routes missing @jwt_required():\n" + "\n".join(violations)


def test_namespace_and_admin_writes_have_role_guards():
    # DOCiD is a self-service PID registry: any authenticated account may mint.
    # Namespace writes therefore need a database-resolved actor (which also
    # populates g.current_user for the mint audit trail) rather than a role
    # gate. Administrative modules still require an explicit admin role.
    required = {
        "cordoi.py": {"database_user_required", "pid_minter_required", "admin_required"},
        "admin_harvest_sources.py": {"admin_required"},
        "arks.py": {"database_user_required", "pid_minter_required"},
        "cstr.py": {"database_user_required", "pid_minter_required"},
        "smtp.py": {"admin_required"},
    }
    violations = []
    for filename, accepted_guards in required.items():
        tree = ast.parse((ROUTES_DIR / filename).read_text())
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            methods = set().union(*(_route_methods(item) for item in node.decorator_list))
            if not methods.intersection(MUTATION_METHODS):
                continue
            decorators = " ".join(ast.unparse(item) for item in node.decorator_list)
            if not any(guard in decorators for guard in accepted_guards):
                violations.append(f"{filename}:{node.lineno} {node.name}")

    assert not violations, "Privileged writes missing a role guard:\n" + "\n".join(violations)
