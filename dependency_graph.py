import csv
import json
import os
import subprocess
from pathlib import Path

class DependencyGraph:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.graphviz_path = self.config["graphviz_path"]
        self.package_path = self.config["package_path"]
        self.output_path = self.config["output_path"]
        self.dependencies = {}

    @staticmethod
    def load_config(config_path):
        """Загружает конфигурацию из CSV."""
        config = {}
        with open(config_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    key, value = row
                    config[key.strip()] = value.strip()
        return config

    def parse_dependencies(self):
        """Извлекает зависимости из package.json и package-lock.json."""
        package_json_path = Path(self.package_path) / "package.json"
        package_lock_path = Path(self.package_path) / "package-lock.json"

        if not package_json_path.exists() or not package_lock_path.exists():
            raise FileNotFoundError("Файлы package.json и/или package-lock.json не найдены.")

        with open(package_lock_path, mode="r", encoding="utf-8") as lockfile:
            lock_data = json.load(lockfile)
            self.dependencies = lock_data.get("dependencies", {})

    def build_graph(self):
        """Создает представление графа в формате DOT."""
        lines = ["digraph G {"]
        lines.append('    graph [rankdir=LR];')
        lines.append('    node [shape=box, style=rounded];')

        def add_edges(dep_name, dep_data):
            if "dependencies" in dep_data:
                for sub_dep_name in dep_data["dependencies"]:
                    lines.append(f'    "{dep_name}" -> "{sub_dep_name}";')
                    add_edges(sub_dep_name, self.dependencies.get(sub_dep_name, {}))

        for dep_name, dep_data in self.dependencies.items():
            add_edges(dep_name, dep_data)

        lines.append("}")
        return "\n".join(lines)

    def generate_graph_image(self):
        """Генерирует изображение графа с использованием Graphviz."""
        dot_file = Path(self.output_path).with_suffix(".dot")
        png_file = Path(self.output_path)

        # Создание файла .dot
        graph_dot = self.build_graph()
        with open(dot_file, mode="w", encoding="utf-8") as dotfile:
            dotfile.write(graph_dot)

        # Вызов Graphviz для генерации изображения
        try:
            subprocess.run(
                [self.graphviz_path, "-Tpng", str(dot_file), "-o", str(png_file)],
                check=True,
            )
            print(f"Граф успешно сохранен в {png_file}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ошибка при вызове Graphviz: {e}")

    def run(self):
        """Основной метод запуска обработки."""
        self.parse_dependencies()
        self.generate_graph_image()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Визуализатор графа зависимостей для npm.")
    parser.add_argument(
        "config", type=str, help="Путь к конфигурационному файлу CSV"
    )
    args = parser.parse_args()

    try:
        graph = DependencyGraph(args.config)
        graph.run()
    except Exception as e:
        print(f"Ошибка: {e}")
