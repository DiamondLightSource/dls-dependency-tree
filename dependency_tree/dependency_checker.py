#!/bin/env python2.4

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
from qt import *
from tree import dependency_tree
from tree_update import dependency_tree_update
from dependency_checker_gui import Form1
from subprocess import Popen, PIPE

class ButtonListItem(QListViewItem):
    """Custom ListViewItem with options to change base and text colours"""
    def paintCell(self, painter, cg, column, width, align):
        # taken from Diamon web page css
        grp = QColorGroup(cg)
        grp.setColor(QColorGroup.Base, self.base_color)
        grp.setColor(QColorGroup.Text, self.text_color)
        QListViewItem.paintCell(self, painter, grp, column, width, align)

def build_gui_tree(list_view,tree,parent=None):
    """Function that takes a ListView or ListViewItem, and populates its
    children from a dependency_tree"""
    if parent==None:
        list_view.clear()
    if parent:
        child = ButtonListItem(parent, tree.name+": "+tree.version)
    else:
        child = ButtonListItem(list_view, tree.name+": "+tree.version)
        list_view.child = child
    child.tree = tree
    child.setSelectable(False)
    child.text_color = Qt.black
    child.base_color = QColor(212,216,236) # normal - blue
    open_parents = False
    if len(tree.updates())>1:
        child.base_color = QColor(203,255,197) # update available - green
        open_parents = True
    if tree.name in list_view.clashes.keys():
        open_parents = True
        if tree.path == tree.e.sortReleases([x.path for x in \
                                             list_view.clashes[tree.name]])[-1]:
            child.text_color = QColor(153,150,0) # involved in clash: yellow
        else:
            child.text_color = Qt.red # causes clash: red
    if tree.version == "invalid":
        open_parents = True
        child.text_color = QColor(160,32,240) # invalid: purple
    if open_parents: 
        temp_ob = child
        while temp_ob.parent():
            list_view.setOpen(temp_ob.parent(),True)
            temp_ob = temp_ob.parent()
    for leaf in tree.leaves:
        build_gui_tree(list_view,leaf,child)
    if parent==None:
        list_view.setOpen(child,True)

class TreeView(QListView):
    """Custom tree view widget"""
    def __init__(self,tree,tree_type,*args):
        """Initialise the class.
        tree = dependency_tree to initialise from
        tree_type = string "original","consistent" or "latest" """
        QListView.__init__(self,*args)
        self.addColumn("%s Tree"%(tree_type.title()))
        self.setPaletteBackgroundColor(QColor(212,216,236))
        self.tree = tree
        self.clashes = tree.clashes(print_warnings=False)
        self.setRootIsDecorated(True)
        self.setSorting(-1)
        # connect event handlers
        QObject.connect(self, SIGNAL("onItem(QListViewItem *)"), self.mousein)
        QObject.connect(self, SIGNAL("contextMenuRequested ( QListViewItem *,"\
                                     "const QPoint &,int)"), self.contextMenu)
        QObject.connect(self, SIGNAL("onViewport()"), self.mouseout)
        build_gui_tree(self,tree)
        self.setOpen(self.child,True)

    def contextMenu(self, item, pos, col):
        """Popup a context menu at pos, fill it with svn log and revert commands
        depending on the module it is and what version it's at"""
        if item:
            menu = QPopupMenu()
            self.contextItem = item
            menu.insertItem("Edit RELEASE", self.externalEdit)
            if hasattr(item.tree,"versions"):
                if item.tree.version!=item.tree.versions[0][0]:
                    menu.insertItem("SVN log", self.svn_log)
                self.context_methods = []
                for version,path in [(v,p) for v,p in item.tree.versions \
                                     if v!=item.tree.version]:
                    self.context_methods.append(reverter(item.tree,self,path))
                    menu.insertItem("Change to %s"%version, \
                                    self.context_methods[-1].revert)
            menu.exec_loop(pos)

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
        x.setCaption("SVN Log: %s"%leaf.name)
        x.show()        

    def externalEdit(self):
        """Open the configure/RELEASE in gedit"""
        item = self.contextItem
        if item and os.path.isfile(item.tree.release()):
            text = "gedit "+item.tree.release()
            args = QStringList()
            for a in text.split():
                args.append(a)
            proc = QProcess(args, self)
            proc.launch("")
                                        
    def mouseout(self):
        """Show hints in the statusBar on mouseout"""
        self.top.statusBar().message("----- Hover over a module for its path, "\
                                     "right click for a context menu -----")
                
    def mousein(self, item):
        """Show item path in the statusBar on mousein"""
        text = item.tree.name+" - current: "+item.tree.path
        if len(item.tree.updates())>1:
            text += ", latest: "+item.tree.updates()[-1]
        self.top.statusBar().message(text)

    def confirmWrite(self):
        """Popup a confimation box for writing changes to RELEASE"""
        response=QMessageBox.question(None,"Write Changes",\
             "Would you like to write your changes to configure/RELEASE?",\
             QMessageBox.Yes,QMessageBox.No)
        if response == QMessageBox.Yes:
            self.update.write_changes()

    def printChanges(self):
        text = self.update.print_changes()
        x = formLog(text,self)
        x.setCaption("RELEASE Changes")
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

class formLog(QDialog):
    """SVN log form"""
    def __init__(self,text,parent = None,name = None,modal = 0,fl = 0):
        """text = text to display in a readonly QTextEdit"""
        QDialog.__init__(self,parent,name,modal,fl)
        formLayout = QGridLayout(self,1,1,11,6,"formLayout")
        self.scroll = QScrollView(self)        
        self.lab = QTextEdit()
        self.lab.setFont(QFont('monospace', 10))
        self.lab.setText(text)
        self.lab.setReadOnly(True)
        self.scroll.addChild(self.lab)
        self.scroll.setResizePolicy(QScrollView.AutoOneFit)
        self.scroll.setMinimumWidth(700)        
        formLayout.addWidget(self.scroll,1,1)        
        self.btnClose = QPushButton(self,"btnClose")
        formLayout.addWidget(self.btnClose,2,1)
        self.clearWState(Qt.WState_Polished)
        self.connect(self.btnClose,SIGNAL("clicked()"),self.close)
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
        
    app = QApplication([])
    top = Form1()
    tree = dependency_tree(None,path)
    grid = QVBoxLayout(top.originalFrame)
    grid.setAutoAdd(True)
    view = TreeView(tree,"original",top.originalFrame)
    view.top = top
    view.mouseout()    
    top.setCaption("Tree Browser - "+tree.name+": "+tree.version+", Epics:"+\
                   tree.e.epicsVer())
    
    for loc in ["latest","consistent"]:
        def displayMessage(message):
            getattr(top,loc+"Write").setEnabled(False)
            getattr(top,loc+"Print").setEnabled(False)
            label = QTextEdit(getattr(top,loc+"Frame"))
            label.setReadOnly(True)
            label.setText(loc.title() + " Updated Tree:\n\n" + message)
        try:
            grid = QVBoxLayout(getattr(top,loc+"Frame"))
            grid.setAutoAdd(True)        
            update = dependency_tree_update(tree,consistent=(loc=="consistent"))
            if not update.new_tree == tree:
                view = TreeView(update.new_tree,loc,getattr(top,loc+"Frame"))
                view.top = top
                view.update = update
                QObject.connect(getattr(top,loc+"Write"), SIGNAL("clicked()"),\
                                view.confirmWrite)
                QObject.connect(getattr(top,loc+"Print"), SIGNAL("clicked()"),\
                                view.printChanges)        
            else:
                displayMessage("Updated tree is identical to Original tree")
        except:
                displayMessage("Error in tree update...\n\n"+traceback.format_exc())
    top.show()
    app.setMainWidget(top)
    # catch CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec_loop()
                                                        
if __name__ == "__main__":
    from pkg_resources import require
    require("dls.environment==1.0")
    dependency_checker()
