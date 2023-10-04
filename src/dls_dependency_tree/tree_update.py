#!/bin/env dls-python
"""Script to update the dependency tree."""
import os
import shutil
from typing import Dict, List, Optional

from .tree import dependency_tree


class dependency_tree_update:
    """Class for updating a dependency_tree object."""

    #############
    # Variables #
    #############
    # old_tree: original dependency_tree
    # new_tree: updated dependency_tree

    def __init__(
        self, tree: dependency_tree, consistent: bool = True, update: bool = True
    ) -> None:
        """Take a dependency_tree and update every module to its latest version.

        If consistent is True, it then roll back versions of the updated modules
        until they form a consistent set
        """
        # dict of lists of paths for each module
        # - self.differences[module][0]=old_tree_module.path
        # - self.differences[module][-1]=new_tree_module.path
        self.differences: Dict[str, List[str]] = {}
        # original dependency_tree object
        self.old_tree: dependency_tree = tree
        self.strict=self.old_tree.strict
        # new updated dependency_tree object
        self.new_tree: dependency_tree = dependency_tree(strict=self.strict)

        if self.old_tree.clashes(print_warnings=False):
            # Message to print if consistency fails
            self.errorMsg: str = (
                "Algorithm not guaranteed to work as original tree"
                " has clashes. Manually revert some modules and "
                "try again."
            )
        else:
            self.errorMsg = "Algorithm fails if too many modules are in work"
        # update to latest version
        self.find_latest()
        if update:
            self.update_tree()
        if consistent:
            # try to make a consistent set
            self.make_consistent()

    def print_changes(self) -> str:
        """Print the changes between releases.

        Print the changes between the RELEASE file of old_tree, and the
        RELEASE file that would be written by new_tree
        """
        message: str = ""
        for i, line in enumerate(self.old_tree.lines):
            new_line = self.new_tree.lines[i]
            if line != new_line:
                message += "Change: " + line + "To:     " + new_line
        print(message)
        return message

    def write_changes(self) -> None:
        """Backup old RELEASE and write new RELEASE.

        Backup the old_tree RELEASE to RELEASE~, and write the new_tree
        RELEASE to RELEASE
        """
        release: str = self.old_tree.release()
        backup_release: str = release + "~"
        if os.path.isfile(backup_release):
            os.remove(backup_release)
        shutil.copy(release, backup_release)
        print("Backup written to:", backup_release)
        file = open(release, "w")
        file.writelines(self.new_tree.lines)
        file.close()
        print("Changes written to:", release)

    def find_latest(self) -> None:
        """Update new_tree to latest versions of everything."""
        self.new_tree = self.old_tree.copy()
        self.differences = {}
        for leaf in self.new_tree.leaves:
            # update each leaf
            leaf_updates = leaf.updates()
            if len(leaf_updates) > 1:
                # if there are updates available, add
                self.differences[leaf.name] = leaf_updates
                dummy = dependency_tree(None, strict=self.strict)
                leaf.versions = []
                for path in leaf_updates:
                    dummy.path = path
                    dummy.init_version()
                    leaf.versions.append((dummy.version, path))

    def update_tree(self) -> None:
        """Update new_tree to latest versions of everything."""
        for leaf in self.new_tree.leaves:
            if leaf.name in self.differences:
                new_leaf = dependency_tree(leaf.parent, self.differences[leaf.name][-1],
                                           strict=self.strict)
                new_leaf.versions = leaf.versions
                self.new_tree.replace_leaf(leaf, new_leaf)

    def make_consistent(self) -> None:
        """Roll back the changes we made in update_tree() until it is consistent."""
        clashes: Dict[str, List[dependency_tree]] = self.new_tree.clashes(
            print_warnings=False
        )
        agenda: Optional[dependency_tree] = None
        lasti: int = -1
        print("Making a consistent set of releases, press Ctrl-C to interrupt...")
        while clashes:
            if agenda:
                assert agenda.parent, "Module has no parent: " + str(agenda)
                if agenda.parent == self.new_tree:
                    # if the module is listed directly in this tree, try to revert
                    try:
                        self.__revert(agenda)
                        clashes = self.new_tree.clashes(print_warnings=False)
                        agenda = None
                    except AssertionError:
                        lasti -= 1
                        if len(clashes[list(clashes.keys())[0]]) + lasti < 0:
                            raise
                        else:
                            agenda = clashes[list(clashes.keys())[0]][lasti]
                else:
                    # keep stepping up the tree until we find a module we are
                    # allowed to revert
                    agenda = agenda.parent
            else:
                # pick the next module to revert
                lasti = -1
                agenda = clashes[list(clashes.keys())[0]][-1]
        print("Done")

    def __revert(self, leaf: dependency_tree) -> None:
        """Revert leaf by one version."""
        assert leaf.name in self.differences, (
            "Cannot revert module: " + leaf.name + "\n" + self.errorMsg
        )
        paths = self.differences[leaf.name]
        new_leaf_path = paths[-2]
        self.differences[leaf.name] = paths[:-1]
        if len(paths) < 3:
            del self.differences[leaf.name]
        new_leaf = dependency_tree(leaf.parent, new_leaf_path, strict=self.strict)
        print(
            "Reverting %s from %s to %s" % (leaf.name, leaf.version, new_leaf.version)
        )
        new_leaf.versions = leaf.versions
        self.new_tree.replace_leaf(leaf, new_leaf)


# commented out test function
# if __name__=="__main__":
#    tree = dependency_tree(None,"/dls_sw/work/R3.14.8.2/ioc/BL15I/MO/")
#    update_tree = dependency_tree_update(tree,consistent=False)
#    update_tree.print_changes()
#    update_tree.new_tree.clashes()
#    update_tree = dependency_tree_update(tree)
#    update_tree.print_changes()
