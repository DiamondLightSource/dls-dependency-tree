from typing import Optional, Dict, List, Set
from dls_dependency_tree import dependency_tree
from PyQt5 import QtWidgets, QtGui, QtCore
import re
from .constants import NUMBERS_DASHES_DLS_REGEX, NUMBERS_DASHES_REGEX


class VersionSelector(QtWidgets.QWidget):
    def __init__(self, release_path, regex: Optional[str] = None) -> None:
        self.versions: Dict[str, List[str]] = {}
        current_tree = dependency_tree(None, release_path)
        for leaf in current_tree.leaves:
            self.versions[leaf.name] = [Version(path, regex=regex) for path in leaf.updates()]
        super(VersionSelector, self).__init__()

        myBoxLayout = QtWidgets.QGridLayout()
        self.setLayout(myBoxLayout)
        module_number = -1
        self.checkboxes = {}
        self.setting_checkbox_default = True
        for module_name, versions in self.versions.items():
            self.checkboxes[module_name] = []
            module_number += 1
            toolbutton = QtWidgets.QToolButton(self)
            toolbutton.setText(module_name)
            toolmenu = QtWidgets.QMenu(self)
            all_action = toolmenu.addAction("All")
            all_action.module = module_name
            all_action.setCheckable(True)
            all_action.toggled.connect(lambda: self.set_all_for_module(True))
            none_action = toolmenu.addAction("None")
            none_action.module = module_name
            none_action.setCheckable(True)
            none_action.toggled.connect(lambda: self.set_all_for_module(False))
            for version in versions:
                action = toolmenu.addAction("%s" % version)
                action.version = version
                action.setCheckable(True)
                action.toggled.connect(self.onClicked)
                if version.allowed:
                    action.setChecked(True)
                self.checkboxes[module_name].append(action)
            toolbutton.setMenu(toolmenu)
            toolbutton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
            myBoxLayout.addWidget(toolbutton, module_number // 3, module_number % 3)

        toolbutton = QtWidgets.QPushButton(self)
        toolbutton.setText("Check all")
        toolbutton.clicked.connect(lambda: self.set_all_modules(True))
        myBoxLayout.addWidget(toolbutton, module_number // 3 + 1, 0)

        toolbutton = QtWidgets.QPushButton(self)
        toolbutton.setText("Check DLS format")
        toolbutton.clicked.connect(
            lambda: self.set_all_modules(True, NUMBERS_DASHES_DLS_REGEX)
        )
        toolbutton.setToolTip("Check all modules with version name of form 1-2dls3-4")
        myBoxLayout.addWidget(toolbutton, module_number // 3 + 1, 1)

        toolbutton = QtWidgets.QPushButton(self)
        toolbutton.setText("Check number format")
        toolbutton.clicked.connect(
            lambda: self.set_all_modules(True, NUMBERS_DASHES_REGEX)
        )
        toolbutton.setToolTip("Check all modules with version name of form 1-2-3-4")
        myBoxLayout.addWidget(toolbutton, module_number // 3 + 1, 2)

        toolbutton = QtWidgets.QPushButton(self)
        toolbutton.setText("Uncheck all")
        toolbutton.clicked.connect(lambda: self.set_all_modules(False))
        myBoxLayout.addWidget(toolbutton, module_number // 3 + 2, 0)

        self.setting_checkbox_default = False

    def set_all_modules(self, allowed: bool, regex: Optional[str] = None) -> None:
        for module_versions in self.checkboxes.values():
            for button in module_versions:
                if regex is None or bool(re.match(regex, button.version.version)):
                    button.setChecked(allowed)

    def set_all_for_module(self, allowed: bool) -> None:
        sender = self.sender()
        for button in self.checkboxes[sender.module]:
            button.setChecked(allowed)
        sender.setChecked(False)

    def onClicked(self) -> None:
        if self.setting_checkbox_default:
            return
        cbutton = self.sender()
        cbutton.version.allowed = cbutton.isChecked()

    def get_version_numbers(self) -> Dict[str, Set[str]]:
        version_numbers = {}
        for module, versions in self.versions.items():
            version_numbers[module] = set()
            for version in [v for v in versions if v.allowed]:
                version_numbers[module].add(version.version)
        return version_numbers


class Version:
    def __init__(
        self,
        path: str,
        version: Optional[str] = None,
        allowed: Optional[bool] = None,
        regex: Optional[str] = None,
    ):
        self.path = path
        self.version = version or path.split("/")[-1]
        self.allowed = (
            allowed
            if allowed is not None
            else bool(regex is None or re.match(regex, self.version))
        )

    def __repr__(self):
        return self.version
