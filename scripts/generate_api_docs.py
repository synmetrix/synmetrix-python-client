#!/usr/bin/env python
import ast
from pathlib import Path
from typing import Union


class APIDocGenerator:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.source = Path(filepath).read_text()
        self.tree = ast.parse(self.source)

    def _get_docstring(
        self,
        node: Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module],
    ) -> str:
        """Extract docstring from an AST node."""
        docstring = ast.get_docstring(node)
        return docstring.strip() if docstring else ""

    def _format_arguments(
        self, node: Union[ast.AsyncFunctionDef, ast.FunctionDef]
    ) -> str:
        """Format function arguments with their type hints."""
        args = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue

            # Get type annotation if it exists
            if arg.annotation:
                type_hint = ast.unparse(arg.annotation)
                args.append(f"{arg.arg}: {type_hint}")
            else:
                args.append(arg.arg)

        # Handle defaults
        defaults = [None] * (
            len(node.args.args) - len(node.args.defaults)
        ) + node.args.defaults
        for i, default in enumerate(defaults):
            if default and i >= len(node.args.args) - len(node.args.defaults):
                arg_idx = i - (len(defaults) - len(node.args.defaults))
                args[arg_idx] += f" = {ast.unparse(default)}"

        return ", ".join(args)

    def _get_return_type(
        self, node: Union[ast.AsyncFunctionDef, ast.FunctionDef]
    ) -> str:
        """Get the return type annotation if it exists."""
        if node.returns:
            return ast.unparse(node.returns)
        return ""

    def generate_markdown(self) -> str:
        """Generate markdown documentation for the API client."""
        output = ["# API Reference\n\n"]

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == "Client":
                output.append("## Client Class\n\n")

                for method in node.body:
                    if isinstance(method, ast.AsyncFunctionDef):
                        # Skip private methods
                        if method.name.startswith("_"):
                            continue

                        # Method signature
                        return_type = self._get_return_type(method)
                        return_annotation = f" -> {return_type}" if return_type else ""

                        # Split long lines for better readability
                        signature = (
                            f"### `async def {method.name}"
                            f"({self._format_arguments(method)})"
                            f"{return_annotation}`\n"
                        )
                        output.append(signature)

                        # Method docstring
                        docstring = self._get_docstring(method)
                        if docstring:
                            output.append(f"{docstring}\n")

                        # Add separator between methods
                        output.append("---\n\n")

        return "".join(output)


def main():
    client_path = Path("synmetrix_graphql_client/graphql_client/client.py")
    generator = APIDocGenerator(str(client_path))
    docs = generator.generate_markdown()

    # Write to docs/api_reference.md
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "api_reference.md"
    output_file.write_text(docs)
    print(f"API documentation generated at {output_file}")


if __name__ == "__main__":
    main()
