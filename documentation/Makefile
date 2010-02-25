html/index.html: config.src manual.src
	mkdir -p html
	cd html; dls-make-doxygen-documentation.py $^	
	cd html; dls-python-documentation.py -t --src=../../dist/dls.dependency_tree-*.egg dls.dependency_tree	
	
all install: html/index.html
			
clean uninstall:
	rm -rf html					
