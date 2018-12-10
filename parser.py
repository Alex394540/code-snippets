import asyncio
import os
import argparse
import sys
import time

try:
    import aiohttp
    import async_timeout
    import ujson
except ImportError:
    raise Exception("Modules 'aiohttp', 'ujson' and 'async_timeout' are required for this program!")

from contextlib import suppress
from zipfile import BadZipFile, LargeZipFile, ZipFile

from lookup import Finder
from helpers import get_extensions, create_folder, \
                    append_report, get_download_url,\
                    EXTRACT_DESTINATION, TMP_FOLDER, RESULT_FILE

"""
Small program for providing code snippets with specific class/function usage.
All examples are taken from github.com.

If you have notices some bug, or want to propose some improvements, write me:
Facebook - https://www.facebook.com/megleyalex
Vk       - https://vk.com/megley
Gmail    - alibaba394540@gmail.com
"""

__author__ = "Megley Alexey"


async def github_search(module):
    """
    Get information about corresponding repositories via github API
    """
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.github.com/search/repositories', params={'q': module}) as resp:
            return await resp.json(loads=ujson.loads)


async def get_content(url):
    """
    Get content of passed url
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


class Scrapper:

    def __init__(self, language, module, class_name, function_name, wrapper_lines, examples_limit):
        self.language = language
        self.module = module
        self.class_name = class_name
        self.function_name = function_name
        self.wrapper_lines = wrapper_lines
        self.examples_limit = examples_limit
        self.examples_found = 0

    async def scrap_repo(self, session, url, repo):

        # drop connection in 60 seconds
        with async_timeout.timeout(60):
            async with session.get(url) as response:
                name = str(time.time()) + '.zip'
                filename = os.path.join(TMP_FOLDER, name)
                with open(filename, 'wb') as f_handle:

                    # write file chunk by chunk...
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f_handle.write(chunk)

                # create unique directory where zip will be extracted...
                destination = os.path.join(EXTRACT_DESTINATION, name[:-4])
                os.makedirs(destination, exist_ok=True)

                # extract zip
                with suppress(BadZipFile, LargeZipFile):
                    ZipFile(filename).extractall(destination)

                # find occurrences in downloaded project
                finder = Finder(working_directory=destination, class_name=self.class_name, func_name=self.function_name,
                                current_repo=repo, extensions=get_extensions(self.language),
                                lines_around=self.wrapper_lines, examples_limit=self.examples_limit)

                found, report = finder.explore_repository()
                print("Repository - {}. {} occurrences was found!".format(repo, found))
                return found, report

    async def find_usages(self):
        """
        Try to find examples with usages of typed class/function on github
        """
        result_report = RESULT_FILE + get_extensions(self.language)[0]

        # remove old report
        with suppress(IOError):
            os.mkdir(TMP_FOLDER)
            os.remove(result_report)

        # get repositories for the module
        response = await github_search(self.module)
        repos = [(get_download_url(repo['full_name']), repo['full_name']) for repo in response['items']]

        with create_folder(TMP_FOLDER), create_folder(EXTRACT_DESTINATION):
            async with aiohttp.ClientSession(loop=loop) as session:

                # start scrapping asynchronously
                tasks = [self.scrap_repo(session, url, repo) for url, repo in repos]
                data_available = True
                while data_available:

                    # извлеки выполненные задачи
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                    # запусти поиск на них
                    for found, report in [task.result() for task in done]:
                        self.examples_found += found
                        append_report(result_report, report)
                        if self.examples_found >= self.examples_limit:
                            for task in pending:
                                task.cancel()
                            data_available = False

                    if not pending:
                        break

                    tasks = pending


if __name__ == "__main__":

    if sys.version_info < (3, 5):
        raise Exception("Python with version 3.5+ is required for running this program!")

    parser = argparse.ArgumentParser()
    parser.add_argument('language', help='Name of programming language')
    parser.add_argument('module', help='Name of module')

    parser.add_argument('-c', '--class_name', nargs='?', help='Name of the class to be searched')
    parser.add_argument('-f', '--function', nargs='?', help='Name of the function to be searched')

    parser.add_argument('-l', '--lines_around', nargs='?', const='const-one', default=5, type=int,
                        help='Lines around found occurrence')
    parser.add_argument('-e', '--examples', nargs='?', const='const-one', default=10, type=int,
                        help='The amount of the snippets')

    args = parser.parse_args()

    if bool(args.function) == bool(args.class_name):
        parser.error('Wrong amount of arguments to be searched. Either class or function should be specified.')

    msg = "{decor} Searching {examples} snippets of size {size} containing {obj} from module '{module}' {decor}".format(
        examples=args.examples, size=2*args.lines_around, module=args.module, decor='=' * 20,
        obj="function '{}'".format(args.function) if args.function else "class '{}'".format(args.class_name)
    )

    print(msg)

    scrapper = Scrapper(args.language, args.module, args.class_name, args.function, args.lines_around, args.examples)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(scrapper.find_usages())
