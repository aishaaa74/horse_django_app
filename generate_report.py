"""
Генерирует Word-отчёт по всем тестам приложения tours.

Запуск (из корня проекта, после установки django и python-docx):
    python generate_report.py

Результат: django_test_report.docx рядом с этим скриптом.
"""

import inspect
import os
import textwrap
import unittest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from docx import Document  # noqa: E402
from docx.shared import Pt  # noqa: E402


def iter_tests(suite):
    """Рекурсивно достаёт отдельные тесты из TestSuite."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def main():
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tours", pattern="test*.py")

    by_class = {}
    for test in iter_tests(suite):
        cls = test.__class__
        method_name = getattr(test, "_testMethodName", None)
        if not method_name:
            continue
        method = getattr(cls, method_name, None)
        if method is None:
            continue
        by_class.setdefault(cls, []).append((method_name, method))

    doc = Document()
    doc.add_heading("Отчёт по тестам проекта «Конные туры»", level=0)

    total = 0
    for cls, methods in by_class.items():
        doc.add_heading(cls.__name__, level=1)
        if cls.__doc__:
            doc.add_paragraph(inspect.cleandoc(cls.__doc__))

        for name, method in sorted(methods):
            total += 1
            doc.add_heading(name, level=2)
            if method.__doc__:
                doc.add_paragraph(inspect.cleandoc(method.__doc__))
            try:
                source = textwrap.dedent(inspect.getsource(method))
            except (OSError, TypeError):
                source = "(исходный код недоступен)"
            p = doc.add_paragraph()
            run = p.add_run(source)
            run.font.name = "Consolas"
            run.font.size = Pt(9)

    doc.add_paragraph(f"Всего тестов: {total}")

    output = Path(__file__).resolve().parent / "django_test_report.docx"
    doc.save(output)
    print(f"Готово: {output} (тестов: {total})")


if __name__ == "__main__":
    main()
