import argparse
import os
import hashlib
import zlib
import json
import shutil

class SimpleGit:
    def __init__(self, repo_path):
        self.repo_path = os.path.abspath(repo_path)
        self.git_dir = os.path.join(self.repo_path, ".simplegit")
        self.objects_dir = os.path.join(self.git_dir, "objects")
        self.staged_files_path = os.path.join(self.git_dir, "index.json")
        self.staged_files = self._load_staged_files()

    def _load_staged_files(self):
        if os.path.exists(self.staged_files_path):
            with open(self.staged_files_path, "r") as f:
                return json.load(f)
        return {}

    def _save_staged_files(self):
        with open(self.staged_files_path, "w") as f:
            json.dump(self.staged_files, f)

    def init(self):
        if not os.path.exists(self.git_dir):
            # Create Objects Dir
            os.makedirs(self.objects_dir, exist_ok=True)
            # Create Objects HEAD
            with open(os.path.join(self.git_dir, "HEAD"), "w") as f:
                f.write("ref: refs/heads/master\n")
            # Create Objects refs
            os.makedirs(os.path.join(self.git_dir, "refs", "heads"), exist_ok=True)
            print(f"Made a new Git-like place in {self.repo_path}")
        else:
            print("Already a Git-like place here.")

    def _save_object(self, data, obj_type="blob"):
        header = f"{obj_type} {len(data)}\0".encode("utf-8")
        full_content = header + data
        object_hash = hashlib.sha1(full_content).hexdigest()
        compressed_content = zlib.compress(full_content)

        object_dir = os.path.join(self.objects_dir, object_hash[:2])
        object_path = os.path.join(object_dir, object_hash[2:])
        os.makedirs(object_dir, exist_ok=True)
        with open(object_path, "wb") as f:
            f.write(compressed_content)
        return object_hash

    def add(self, file_path):
        full_path = os.path.join(self.repo_path, file_path)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                file_content = f.read()
            object_hash = self._save_object(file_content)
            self.staged_files[file_path] = object_hash
            self._save_staged_files()
            print(f"Staged: {file_path}")
        else:
            print(f"File not found: {file_path}")

    def commit(self, message):
        if not self.staged_files:
            print("Nothing to commit! Please stage files.")
            return

        tree_content = "\n".join(f"100644 blob {hash} {file}" for file, hash in self.staged_files.items()).encode("utf-8")
        tree_hash = self._save_object(tree_content, "tree")

        commit_message = f"\ntree {tree_hash}\nauthor User <user@example.com> {int(os.times().system + os.times().user)} +0000\ncommitter User <user@example.com> {int(os.times().system + os.times().user)} +0000\n\n{message}\n".encode("utf-8")
        commit_hash = self._save_object(commit_message, "commit")

        branch_ref = os.path.join(self.git_dir, "refs/heads/master")
        with open(branch_ref, "w") as f:
            f.write(commit_hash)

        self.staged_files.clear()
        self._save_staged_files()
        print(f"Committed: {commit_hash}")

    def reset(self, commit_hash):
        branch_ref = os.path.join(self.git_dir, "refs/heads/master")
        if not os.path.exists(os.path.join(self.objects_dir, commit_hash[:2], commit_hash[2:])):
            print(f"Commit {commit_hash} not found.")
            return

        with open(branch_ref, "w") as f:
            f.write(commit_hash)

        self._restore_working_directory(commit_hash)
        self.staged_files.clear()
        self._save_staged_files()
        print(f"Reset to commit {commit_hash[:7]}")

    def _restore_working_directory(self, commit_hash):
        tree_hash = self._get_tree_hash_from_commit(commit_hash)
        if tree_hash:
            files = self._get_files_from_tree(tree_hash)
            for file_path, obj_hash in files.items():
                file_content = self._get_file_content_from_hash(obj_hash)
                full_path = os.path.join(self.repo_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding='utf-8') as f:
                    f.writelines(file_content)
            self._remove_extra_files(files)

    def _remove_extra_files(self, files):
        for root, dirs, filenames in os.walk(self.repo_path):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, self.repo_path)
                if relative_path.startswith(".simplegit"):
                    continue
                if relative_path not in files:
                    os.remove(full_path)

    def _get_tree_hash_from_commit(self, commit_hash):
        commit_path = os.path.join(self.objects_dir, commit_hash[:2], commit_hash[2:])
        if os.path.exists(commit_path):
            with open(commit_path, "rb") as f:
                commit_data = zlib.decompress(f.read()).decode("utf-8")
            for line in commit_data.splitlines():
                if line.startswith("tree "):
                    return line.split(" ")[1]
        return None

    def _get_files_from_tree(self, tree_hash):
        tree_path = os.path.join(self.objects_dir, tree_hash[:2], tree_hash[2:])
        files = {}
        if os.path.exists(tree_path):
            with open(tree_path, "rb") as f:
                tree_data = zlib.decompress(f.read()).decode("utf-8")
            for line in tree_data.splitlines():
                mode, no, obj_type, obj_hash, file_path = line.split(" ")
                files[file_path] = obj_hash
        return files

    def _get_file_content_from_hash(self, obj_hash):
        obj_path = os.path.join(self.objects_dir, obj_hash[:2], obj_hash[2:])
        if os.path.exists(obj_path):
            with open(obj_path, "rb") as f:
                data = zlib.decompress(f.read()).decode("utf-8").split("\0", 1)[1].splitlines()
            return data
        return []