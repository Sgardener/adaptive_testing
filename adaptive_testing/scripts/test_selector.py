#!/usr/bin/env python3
import os
import sys
import subprocess
import yaml

GIT_CMD = r"C:\Program Files\Git\mingw64\bin\git.exe"

#test line
def run_git(cmd):
    try:
        result = subprocess.run([GIT_CMD] + cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        return None

def get_changed_files(target_branch, source_branch):
    # Обновляем информацию о ветках
    run_git(["fetch", "origin"])
    # Сравниваем ветки через origin/...
    diff_range = f"origin/{target_branch}..origin/{source_branch}"
    output = run_git(["diff", "--name-only", diff_range])
    if output is None:
        return None
    files = output.split('\n')
    # Нормализуем слеши
    files = [f.replace('\\', '/') for f in files if f]
    return files

def load_rules(rules_path=".test-rules.yml"):
    if not os.path.exists(rules_path):
        return {"default": {"tests": ["tests/smoke/test_smoke.py"]}}
    with open(rules_path, 'r') as f:
        return yaml.safe_load(f)

def classify_changes(changed_files, rules):
    tests = set()
    for file in changed_files:
        matched = False
        for rule in rules.get('rules', []):
            for pattern in rule.get('paths', []):
                # Обработка wildcard '**' (папка и всё внутри)
                if pattern.endswith('/**'):
                    if file.startswith(pattern[:-2]) or file.startswith(pattern[:-2].replace('\\', '/')):
                        tests.update(rule.get('tests', []))
                        matched = True
                        break
                # Точное совпадение или начало пути
                elif pattern in file or file.startswith(pattern):
                    tests.update(rule.get('tests', []))
                    matched = True
                    break
            if matched:
                break
        if not matched and rules.get('default'):
            tests.update(rules['default'].get('tests', []))
    return list(tests)

def save_selected_tests(tests, output_file="selected_tests.txt"):
    with open(output_file, 'w') as f:
        for test in tests:
            f.write(test + '\n')

def save_log(changed_files, tests, log_file="test-selection.log"):
    with open(log_file, 'w') as f:
        f.write("=== АДАПТИВНЫЙ ВЫБОР ТЕСТОВ ===\n")
        f.write(f"Изменённые файлы ({len(changed_files)}):\n")
        for file in changed_files[:20]:
            f.write(f"  - {file}\n")
        f.write("Выбранные тесты:\n")
        for test in tests:
            f.write(f"  - {test}\n")
        f.write("=== КОНЕЦ ЛОГА ===\n")

def fallback_all_tests():
    """Запуск всех тестов (fallback)"""
    print("FALLBACK: запуск всех тестов")
    with open("selected_tests.txt", "w") as f:
        f.write("tests/\n")
    with open("test-selection.log", "w") as f:
        f.write("FALLBACK: все тесты\n")

def main():
    # Получаем ветки из переменных окружения GitLab CI
    target = os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME") or os.environ.get("CI_DEFAULT_BRANCH", "main")
    source = os.environ.get("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME") or os.environ.get("CI_COMMIT_BRANCH", "HEAD")
    print(f"Target branch: {target}, Source branch: {source}")

    changed = get_changed_files(target, source)
    if changed is None:
        print("Ошибка получения изменённых файлов, используем fallback")
        fallback_all_tests()
        return
    if not changed:
        print("Нет изменений или ошибка, используем fallback")
        fallback_all_tests()
        return
    
    rules = load_rules()
    tests = classify_changes(changed, rules)
    if not tests:
        print("Тесты не выбраны, используем fallback")
        fallback_all_tests()
        return
    
    save_selected_tests(tests)
    save_log(changed, tests)
    print("Созданы артефакты: selected_tests.txt, test-selection.log")
    # Принудительно выводим содержимое для отладки
    with open("selected_tests.txt", 'r') as f:
        print("selected_tests.txt содержит:", f.read())
    with open("test-selection.log", 'r') as f:
        print("test-selection.log содержит:\n", f.read())

if __name__ == "__main__":
    main()