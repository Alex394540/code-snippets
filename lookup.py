import re
import os
from contextlib import suppress
from helpers import build_file_url


class Finder:
    """
    Class for finding usages of the given class or function
    in the specific directory and building resulting file
    """

    def __init__(self, *, working_directory, class_name, func_name, current_repo,
                 extensions, lines_around, examples_limit):

        self.working_dir = working_directory
        self.class_name = class_name
        self.function = func_name
        self.current_repo = current_repo
        self.extensions = extensions
        self.lines_around = lines_around
        self.examples_limit = examples_limit
        self.examples_found = 0

    def enough_examples(self):
        return self.examples_found == self.examples_limit

    def has_right_extension(self, file):
        return any((file.endswith(ext) for ext in self.extensions))

    def pattern_found(self, line):
        if '#' in line:
            return None
        pattern = ('[ (\.]' + self.function + '\(') if self.function else ('[ (\.]' + self.class_name + '[\.(]')
        return re.search(pattern, line)

    def get_report_footer(self, file_name):
        file_url = build_file_url(self.current_repo, file_name)
        report_separator = '_' * 130
        report_footer = "\nOriginal file: {url}\n\n{sep}".format(url=file_url, sep=report_separator)
        return report_footer

    def build_line(self, line_number, line, occurrence_line):
        pointer = '<----------------' if line_number == occurrence_line and self.lines_around > 3 else ''
        number = str(line_number).ljust(4, ' ')
        uncommented_line = line.replace('"""', '').replace("'''", '').replace('/*', '')
        result_line = "{num}{line}  {appendix}\n".format(num=number, line=uncommented_line, appendix=pointer)
        return result_line

    def pretty_format(self, target_file, occurrence_line, snippet):
        """
        Building report for the given file
        """
        file_report = "\n\n"
        snippet_lines = snippet.splitlines()

        snippet_start = max(1, occurrence_line - self.lines_around)
        snippet_end = occurrence_line + self.lines_around + 1

        for current_num, line in zip(range(snippet_start, snippet_end), snippet_lines):
            file_report += self.build_line(current_num, line, occurrence_line)

        file_report += self.get_report_footer(target_file)
        return file_report

    def get_entries(self, file_name):
        """
        Find entries of class/function usage in the given file
        """
        entries = []
        with open(file_name, 'r') as f:
            file_content = f.readlines()

        current_line, total_lines = 0, len(file_content)

        while current_line < total_lines:
            if self.pattern_found(file_content[current_line]):

                snippet_start = max(1, current_line - self.lines_around)
                snippet_end = min(total_lines, current_line + self.lines_around + 1)

                whole_snippet = ''.join(file_content[snippet_start:snippet_end])
                entries.append((current_line, whole_snippet,))
                self.examples_found += 1
                if self.enough_examples():
                    return entries

                current_line += self.lines_around

            current_line += 1
        return entries

    def explore_repository(self):
        """
        Find class/function usages in the extracted repository
        """
        report = ""
        for address, dirs, files in os.walk(self.working_dir):
            for file in files:
                if self.has_right_extension(file):
                    target_file = os.path.join(address, file)
                    with suppress(UnicodeDecodeError):
                        occurrences = self.get_entries(target_file)
                        for line, text in occurrences:
                            report += self.pretty_format(target_file, line, text)

                        if self.enough_examples():
                            return self.examples_found, report

        return self.examples_found, report
