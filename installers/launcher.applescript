-- C-MAGE launcher
--
-- Compiled into C-MAGE.app by installers/make-app.sh. Starts the local web
-- interface in a Terminal window and lets the server open the browser.
-- The Terminal window is also how the user stops it.
--
-- Placeholders are substituted at compile time.

property repoDir : "__REPO_DIR__"
property pythonBin : "__PYTHON_BIN__"

on run
	set cmd to "cd " & quoted form of repoDir & " && " & ¬
		quoted form of pythonBin & " webui/server.py"
	tell application "Terminal"
		activate
		do script cmd
	end tell
end run
