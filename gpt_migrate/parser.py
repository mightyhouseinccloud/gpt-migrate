import subprocess
import typer
from yaspin import yaspin
from pathlib import Path
from tree_sitter import Language, Parser, Node
from collections.abc import Iterator

from config import EXTENSION_TO_TREE_SITTER_GRAMMAR_REPO, EXTENSION_TO_LANGUAGE

def decompose_file(file_path: str) -> Iterator[Node]:
    # Do a first-level parse tree decomposition of the file at file_path
    with yaspin(text="Decomposing file", spinner="dots") as spinner:
        repo_url = EXTENSION_TO_TREE_SITTER_GRAMMAR_REPO.get(file_path.split('.')[-1])

        if not repo_url:
            success_text = typer.style(
                f"Couldn't find tree-sitter grammar for programming language {EXTENSION_TO_LANGUAGE.get(file_path.split('.')[-1])}. Aborting decomposition of file.",
                fg=typer.colors.RED,
            )
            typer.echo(success_text)

        repo_name = repo_url.split('/')[-1]
        if not Path(f"cache/tree-sitter/{repo_name}").exists():
            Path("cache/tree-sitter").mkdir(parents=True, exist_ok=True)
            result = subprocess.run(["git", "clone", repo_url], cwd="cache/tree-sitter", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True)

        grammar_lib_path = Path("cache/tree-sitter/my-languages.so")
        if grammar_lib_path.exists():
            grammar_lib_path.unlink()

        Language.build_library(
            'cache/tree-sitter/my-languages.so',
            [f'cache/tree-sitter/{repo_name}'],
        )

        lang = Language('cache/tree-sitter/my-languages.so', repo_url.split('-')[-1])
        parser = Parser()
        parser.set_language(lang)

        source_code = Path(file_path).read_text()
        tree = parser.parse(bytes(source_code, "utf8"))

        root_node = tree.root_node

        yield from root_node.children
        spinner.ok("✅ ")

