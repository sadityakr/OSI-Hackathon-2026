"""Print plain text of a .docx (zip of XML) without executing anything; arg: path."""
import sys, zipfile, re
x = zipfile.ZipFile(sys.argv[1]).read("word/document.xml").decode("utf8")
x = re.sub(r"</w:p>", "\n", x); x = re.sub(r"<[^>]+>", "", x)
open(sys.argv[2],"w",encoding="utf8").write(x)
