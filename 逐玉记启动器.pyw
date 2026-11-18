# -*- coding: utf-8 -*-
"""逐玉记 · 桌面启动器（双击即玩）
================================================
古朴青玉风格的启动界面，点「开始游戏」启动 Sandlight 0.23+。
用 venv pythonw 运行（无控制台黑框）。游戏启动后本窗口最小化，
游戏关闭时启动器自动退出。
"""
import os, sys, subprocess
import tkinter as tk
from tkinter import font as tkfont

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, 'demo_v23ext.py')
VENV_PY = r'C:\Users\Administrator\Documents\ChatGPT\Aholo 3dGame competition\SandlightDemo\.venv\Scripts\python.exe'
PY = VENV_PY if os.path.exists(VENV_PY) else sys.executable
ICO = os.path.join(HERE, '逐玉记.ico')

BG      = '#2D251B'   # 深褐
PANEL   = '#3C3226'
GOLD    = '#F1CE92'
JADE    = '#A8C9BC'
DARK    = '#1A1610'


def start_game():
    btn.config(text='载入中…', state='disabled')
    root.update_idletasks()
    try:
        # 工作目录切到 SandlightDev（游戏资源相对路径依赖）
        proc = subprocess.Popen([PY, GAME], cwd=HERE)
        root.iconify()                      # 最小化启动器
        def watch():
            if proc.poll() is None:
                root.after(1000, watch)
            else:
                root.destroy()              # 游戏关了，启动器一起退出
        root.after(1000, watch)
    except Exception as e:
        btn.config(text='启动失败：%s' % e, state='normal')


root = tk.Tk()
root.title('逐玉记 · 良渚王城')
root.geometry('520x560')
root.resizable(False, False)
root.configure(bg=BG)
if os.path.exists(ICO):
    try: root.iconbitmap(ICO)
    except Exception: pass

# 顶部玉琮图标 + 标题
try:
    img = tk.PhotoImage(file=os.path.join(HERE, 'assets_new', 'ui', 'icon_cong.png'))
    img = img.subsample(max(1, img.width()//96), max(1, img.height()//96))
    tk.Label(root, image=img, bg=BG).pack(pady=(34, 6))
except Exception:
    pass

f_title = tkfont.Font(family='LiSu', size=40, weight='bold')
f_en    = tkfont.Font(family='Georgia', size=13)
f_body  = tkfont.Font(family='SimYou', size=13)
f_btn   = tkfont.Font(family='LiSu', size=24, weight='bold')

tk.Label(root, text='逐 玉 记', font=f_title, fg=GOLD, bg=BG).pack()
tk.Label(root, text='J A D E   H U N T E R', font=f_en, fg=JADE, bg=BG).pack(pady=(0, 18))

# 分隔线
tk.Frame(root, bg=JADE, height=1, width=360).pack(pady=8)

tk.Label(root, text='洪水将临 · 以玉通神 · 守此良渚',
         font=f_body, fg=GOLD, bg=BG).pack(pady=(14, 6))
intro = ('你是良渚之王。与长者交谈，疏通水渠，\n'
         '备粮筑堤，雨后拾玉，登台献祭；\n'
         '亦可往西外环荒原，命武士讨伐岩石巨怪。')
tk.Label(root, text=intro, font=f_body, fg=JADE, bg=BG,
         justify='center').pack(pady=10)

# 开始按钮
btn = tk.Button(root, text='开 始 游 戏', font=f_btn,
                fg=DARK, bg=GOLD, activebackground=JADE,
                relief='flat', width=16, height=2,
                cursor='hand2', command=start_game)
btn.pack(pady=(22, 14))

# 操作提示
tk.Frame(root, bg=JADE, height=1, width=360).pack(pady=(4, 10))
tk.Label(root, text='WASD 行 ｜ Shift 疾 ｜ E 互动 ｜ M 圈层 ｜ K 玉契 ｜ H 隐藏界面',
         font=('SimYou', 10), fg=JADE, bg=BG, wraplength=440,
         justify='center').pack()
tk.Label(root, text='靠近巨怪按 E 开战 · F5 存 / F9 读 · Esc 暂停',
         font=('SimYou', 10), fg='#9C8B6A', bg=BG).pack(pady=(4, 0))

root.mainloop()
