#!/bin/env dls-python

author = "Tom Cobb"
usage = """%prog [<module_path>]

<module_path> is the path to the module root or configure/RELEASE file. If it
isn't specified, then the current working directory is taken as the module root.
This program is a graphical diplay tool for the configure/RELEASE tree. It 
displays the current tree in the left pane, an updated tree with all modules at
their latest versions in the right pane, and the latest consistent set of
modules in the middle pane. The user then has the chance to change module 
versions between the original and latest numbers, view SVN logs, and edit 
configure/RELEASE files directly. The updated trees can then be written to 
configure/RELEASE, or the changes printed on the commandline."""

import os, sys, signal, string, new, traceback
from optparse import OptionParser
from PyQt4 import QtCore, QtGui

if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(
        os.path.realpath(__file__), '..', '..', '..', 'dls_environment')))

from tree import dependency_tree
from tree_update import dependency_tree_update
from dependency_checker_ui import Ui_Form1
from subprocess import Popen, PIPE
SIGNAL = QtCore.SIGNAL

def build_gui_tree(list_view,tree,parent=None):
    """Function that takes a ListView or ListViewItem, and populates its
    children from a dependency_tree"""
    if parent==None:
        list_view.clear()
    if parent:
        child = QtGui.QTreeWidgetItem(parent)
    else:
        child = QtGui.QTreeWidgetItem(list_view)
        list_view.child = child
    child.setText(0, "%s: %s" % (tree.name, tree.version))
    child.tree = tree
    fg = QtGui.QBrush(QtCore.Qt.black)
    bg = QtGui.QBrush(QtGui.QColor(212,216,236)) # normal - blue
    open_parents = False
    if len(tree.updates())>1:
        bg = QtGui.QBrush(QtGui.QColor(203,255,197)) # update available - green
        open_parents = True
    if tree.name in list_view.clashes.keys():
        open_parents = True
        if tree.path == tree.e.sortReleases([x.path for x in \
                                             list_view.clashes[tree.name]])[-1]:
            fg = QtGui.QBrush(QtGui.QColor(153,150,0)) # involved in clash: yellow
        else:
            fg = QtGui.QBrush(QtCore.Qt.red) # causes clash: red
    if tree.version == "invalid":
        open_parents = True
        fg = QtGui.QBrush(QtGui.QColor(160,32,240)) # invalid: purple
    child.setForeground(0, fg)        
    child.setBackground(0, bg)        
    if open_parents: 
        temp_ob = child
        while temp_ob.parent():
            temp_ob.parent().setExpanded(True)
            temp_ob = temp_ob.parent()
    for leaf in tree.leaves:
        build_gui_tree(list_view,leaf,child)
    if parent==None:
        child.setExpanded(True)

class TreeView(QtGui.QTreeWidget):
    """Custom tree view widget"""
    def __init__(self,tree,tree_type,*args):
        """Initialise the class.
        tree = dependency_tree to initialise from
        tree_type = string "original","consistent" or "latest" """
        QtGui.QTreeWidget.__init__(self,*args)
        self.setHeaderLabel("%s Tree"%(tree_type.title()))
        palette = self.viewport().palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(212,216,236))
        self.viewport().setPalette(palette)
        self.tree = tree
        self.clashes = tree.clashes(print_warnings=False)
        self.setRootIsDecorated(True)
        # connect event handlers
        self.viewportEntered.connect(self.mouseout)
        build_gui_tree(self,tree)
        self.child.setExpanded(True)
        self.itemEntered.connect(self.mousein)
        self.setMouseTracking(True)

    def contextMenuEvent(self, event):
        """Popup a context menu at pos, fill it with svn log and revert commands
        depending on the module it is and what version it's at"""
        pos = event.globalPos()
        item = self.itemAt(event.pos())
        if item:
            menu = QtGui.QMenu()
            self.contextItem = item
            menu.addAction("Edit RELEASE", self.externalEdit)
            if hasattr(item.tree,"versions"):
                if item.tree.version!=item.tree.versions[0][0]:
                    menu.addAction("SVN log", self.svn_log)
                self.context_methods = []
                for version,path in [(v,p) for v,p in item.tree.versions \
                                     if v!=item.tree.version]:
                    self.context_methods.append(reverter(item.tree,self,path))
                    menu.addAction("Change to %s"%version, \
                                    self.context_methods[-1].revert)
            menu.exec_(pos)

    def svn_log(self):
        """Do a dls-logs-since-release.py to find out the svn logs between the
        original release number and the current release number."""
        leaf = self.contextItem.tree
        args = ["dls-logs-since-release.py","-r",leaf.name]
        if leaf.versions[0][0] != "work":
            args += [leaf.versions[0][0],leaf.version]
        p = Popen(args, stdout = PIPE, stderr = PIPE)
        (stdout, stderr) = p.communicate()
        text = stdout.strip()
        x = formLog(text,self)
        x.setWindowTitle("SVN Log: %s"%leaf.name)
        x.show()        

    def externalEdit(self):
        """Open the configure/RELEASE in gedit"""
        item = self.contextItem
        if item and os.path.isfile(item.tree.release()):
            proc = QtCore.QProcess(self)            
            proc.start("gedit",QtCore.QStringList(item.tree.release()))
                                        
    def mouseout(self):
        """Show hints in the statusBar on mouseout"""
        self.top.statusBar.showMessage("----- Hover over a module for its path, "\
                                     "right click for a context menu -----")
                
    def mousein(self, item, col):
        """Show item path in the statusBar on mousein"""
        text = "%s - current: %s" %(item.tree.name, item.tree.path)
        updates = item.tree.updates()
        if len(updates)>1:
            text += ", latest: %s" % updates[-1]
        self.top.statusBar.showMessage(text)

    def confirmWrite(self):
        """Popup a confimation box for writing changes to RELEASE"""
        response=QtGui.QMessageBox.question(None,"Write Changes",\
             "Would you like to write your changes to configure/RELEASE?",\
             QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
        if response == QtGui.QMessageBox.Yes:
            self.update.write_changes()

    def printChanges(self):
        text = self.update.print_changes()
        x = formLog(text,self)
        x.setWindowTitle("RELEASE Changes")
        x.show() 

class reverter:
    """One shot class to revert a leaf in a list view to path"""
    def __init__(self,leaf,list_view,path):
        """leaf = dependency_tree node to revert
        path = new path to revert to
        list_view = ListViewItem associated with leaf"""
        self.leaf = leaf
        self.list_view = list_view
        self.path = path
        
    def revert(self):
        """Do the revert"""
        new_leaf = dependency_tree(self.leaf.parent,self.path)
        new_leaf.versions = self.leaf.versions
        self.list_view.tree.replace_leaf(self.leaf,new_leaf)
        self.list_view.clashes=self.list_view.tree.clashes(print_warnings=False)
        build_gui_tree(self.list_view,self.list_view.tree)

class formLog(QtGui.QDialog):
    """SVN log form"""
    def __init__(self,text,*args):
        """text = text to display in a readonly QTextEdit"""
        QtGui.QDialog.__init__(self,*args)
        formLayout = QtGui.QGridLayout(self)#,1,1,11,6,"formLayout")
        self.scroll = QtGui.QScrollArea(self)        
        self.lab = QtGui.QTextEdit()
        self.lab.setFont(QtGui.QFont('monospace', 10))
        self.lab.setText(text)
        self.lab.setReadOnly(True)
        self.scroll.setWidget(self.lab)
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumWidth(700)        
        formLayout.addWidget(self.scroll,1,1)        
        self.btnClose = QtGui.QPushButton("btnClose", self)
        formLayout.addWidget(self.btnClose,2,1)
        self.btnClose.clicked.connect(self.close)
        self.btnClose.setText("Close")

def dependency_checker():
    """Parses arguments, intialises treeviews and displays them"""
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        if len(args) == 0:
            path = os.getcwd()
        else:
            parser.error("Invalid number of arguments")
    else:
        path = os.path.abspath(args[0])
        
    app = QtGui.QApplication([])
    top = Ui_Form1()
    window = QtGui.QMainWindow()
    top.setupUi(window)
    top.statusBar = window.statusBar()
    tree = dependency_tree(None,path)
    window.setWindowTitle("Tree Browser - %s: %s, Epics: %s" % (
                            tree.name, tree.version, tree.e.epicsVer()))
    
    for loc in ["original","latest","consistent"]:
        def displayMessage(message):
            getattr(top,loc+"Write").setEnabled(False)
            getattr(top,loc+"Print").setEnabled(False)
            label = QtGui.QTextEdit(getattr(top,loc+"Frame"))
            label.setReadOnly(True)
            label.setText(loc.title() + " Updated Tree:\n\n" + message)
            return label
        grid = QtGui.QGridLayout()            
        try:
            update = dependency_tree_update(tree,consistent=(loc=="consistent"),update=(loc!="original"))
            if loc=="original" or not update.new_tree == tree:
                view = TreeView(update.new_tree,loc,getattr(top,loc+"Frame"))
                view.top = top
                view.update = update
                view.connect(getattr(top,loc+"Write"), SIGNAL("clicked()"),\
                                view.confirmWrite)
                view.connect(getattr(top,loc+"Print"), SIGNAL("clicked()"),\
                                view.printChanges)        
                grid.addWidget(view)                                            
            else:
                grid.addWidget(displayMessage("Updated tree is identical to Original tree"))
                
        except:
            grid.addWidget(displayMessage("Error in tree update...\n\n"+traceback.format_exc()))
        getattr(top,loc+"Frame").setLayout(grid)          
                
    window.show()
    # catch CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec_()
                                                        
if __name__ == "__main__":
    dependency_checker()
