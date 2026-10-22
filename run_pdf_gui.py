"""PyInstaller 入口：用绝对导入启动包。

直接拿 ``src/pdf_gui/main.py`` 打包时，它会被当作顶层脚本，里面的相对导入
（``from .app import App``）在冻结环境里没有父包，启动即报
``ImportError: attempted relative import with no known parent package``。
源码运行仍用 ``python -m pdf_gui``。
"""

from pdf_gui.main import main

if __name__ == "__main__":
    main()
