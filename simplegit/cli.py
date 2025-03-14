import argparse
import os
import hashlib
import zlib
import json
import shutil
from .main import SimpleGit
# ... (SimpleGit class code from the previous response) ...

def main():
    args = parse_args()
    args.func(args)

def parse_args():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command')
    commands.required = True

    init_parser = commands.add_parser('init')
    init_parser.add_argument('repo_path', nargs='?', default='.')
    init_parser.set_defaults(func=init)

    add_parser = commands.add_parser('add')
    add_parser.add_argument('file_path', nargs='+')
    add_parser.set_defaults(func=add)

    commit_parser = commands.add_parser('commit')
    commit_parser.add_argument('-m', '--message', required=True)
    commit_parser.set_defaults(func=commit)

    reset_parser = commands.add_parser('reset')
    reset_parser.add_argument('commit_hash')
    reset_parser.set_defaults(func=reset)

    return parser.parse_args()

def init(args):
    git = SimpleGit(args.repo_path)
    git.init()

def add(args):
    git = SimpleGit(os.getcwd())
    for file_path in args.file_path:
        git.add(file_path)

def commit(args):
    git = SimpleGit(os.getcwd())
    git.commit(args.message)

def reset(args):
    git = SimpleGit(os.getcwd())
    git.reset(args.commit_hash)